# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
	"name": "Tomb Raider 2013 Model Format(.mesh)",
	"author": "aman - support TR2013 mesh file. contains Gh0stBlade's TR2013 Noesis importer, maliwei777's RER mod tool framework with fixes from mariokart64n and sectus",						 
	"version": (0, 7),
	"blender": (2, 71, 0),
	"location": "File > Import-Export",
	"description": "Import/Export Tomb Raider 2013 bones and meshes",
	"warning": "",
	"wiki_url": "",
	"category": "Import-Export"}

"""
Related links:

Usage Notes:


This add-on add a "Misc" panel in the 3D View tool shelf (hit "t" key to show/hide Tools shelf)
 
"""
"""
Credits
	Gh0stBlade: For sharing his code and knowledge of TR2013 file format. This addon contains his TR2013 Noesis importer code. Export function is an extension of his importer code.
	Maliwei777: for his RER mod tool which define the mesh replacement modding method. This make it possible to replace part of character mesh with imported meshes.
	
Logs:
			 "--Original RER Mod Tool 3ds Max script by maliwei777 \n"
			  "--Edited By mariokart64n June 11, 2013 -> Added version switch for RER and Re6 \n"
			  "--v0.21 - Edited by Sectus. Fixed material ID (was a byte, but should be a short) \n"
			  "--Blender addon v0.1 by aman - Converted to blender 2.71 add-on \n"
			  "	  armature/bones weight/uv set up based on psk/psa import 2.2 add-on  from Darknet, flufy3d, camg188\n"
			  "	  export set up based on Pointcache .pc2 export 1.1 add-on from Florian Meyer (tstscr) \n"
			  "--v0.23 aman - fixed missing scene property bug \n"
			  "--v0.24 aman - added Smooth overlap vertex export option for removing hard edge in model \n",  
			  -- TR9 v0.1  aman - support TombRader 2013 ,reset version to 0.1. Added Gh0stBlade's Noesis importer code.
			  -- v0.2 aman - add support for vertex tangent and bi-normal			  
			  -- v0.3 aman - Oct-6-2016, enable new mesh to be append to mesh file and has it own private bone map.
			  -- v0.4 aman - Oct-28-2016 support scene object mesh file
			  -- v0.5 aman - May-3-2022 fixed v4_lara export mesh game crash bug
			  -- v0.6 aman - Feb-21-2023 Export unsupported vertex component as VertexPosition type	 (i.e. Tessellation normal).
			  -- v0.7 aman - Sep-13-2023 Add blender custom normal export support. Smooth overlap vertex should be disabled.
	
	
"""
import bpy
from bpy_extras.io_utils import ExportHelper
from os import remove
import time
import mathutils
import math
from mathutils import *
from math import *
from bpy.props import *
from string import *
from struct import *
from math import *
from bpy.props import *
import re
from operator import itemgetter, attrgetter, methodcaller
 
#output log in to txt file
DEBUGLOG = False

#Options: These are bools that enable/disable certain features! They are global and affect ALL platforms!
#Var							Effect
#Misc
#Mesh Global
fDefaultMeshScale = 1.0			#Override mesh scale (default is 1.0)
bOptimizeMesh = 0				#Enable optimization (remove duplicate vertices, optimize lists for drawing) (1 = on, 0 = off)
#bMaterialsEnabled = 1			#Materials (1 = on, 0 = off)
bRenderAsPoints = 0				#Render mesh as points without triangles drawn (1 = on, 0 = off)
#Vertex Components
bNORMsEnabled = 1				#Normals (1 = on, 0 = off)
bUVsEnabled = 1					#UVs (1 = on, 0 = off)
bCOLsEnabled = 0				#Vertex colours (1 = on, 0 = off)
bSkinningEnabled = 1			#Enable skin weights (1 = on, 0 = off)
#Gh0stBlade ONLY
debug = 0					   #Prints debug info (1 = on, 0 = off)

scale = 1.0
bonesize = 1.0
from bpy_extras.io_utils import unpack_list, unpack_face_list
 
def WriteString(f,s):
	f.write(bytes(s, 'UTF-8'))


def WriteShort(f,v):  #unsigned	   
	f.write(pack('<H',int(v)))

# write signed 16 bits integer
def WriteSShort(f,v):
	f.write(pack('<h',int(v)))


def WriteLong(f,v): #unsigned	 
	f.write(pack('<L',v))

def WriteFloat(f,v):
	f.write(pack('<f',v))
	
def WriteByte(f,v):	 #unsigned	  
	f.write(pack('<B',int(v)))

def ReadByte(f):  #unsigned	   
	return unpack('<B',f.read(1))[0]

def ReadFloat(bstream): 
	return unpack('<f', bstream.read(4))[0]
   
def ReadLong(bstream):	#unsigned	 
	return unpack('<L',bstream.read(4))[0]
		
def ReadShort(bstream): #unsigned	 
	return unpack('<H',bstream.read(2))[0]

# read signed 16 bits integer	
def ReadSShort(bstream, Signed = False):
	return unpack('<h',bstream.read(2))[0]
		
class BoneInfo:
	ID =0#,					--cId;
	Parent = -1#,				--cParent;			// -1 means no parents
	Child =0#,				--cChild;				// child id
	uk1 =0#,				--cUnknown;		physic ?
	uk2 =0#,			--fData[2]; physic ? col
	uk3 =0#,			--fData[2]; physic ?
	rx=0
	ry=0
	rz=0
	scale=0
	Trans = 0#				--vTrans;		

def ReadBoneInfo(bstream):
	Info = BoneInfo()
	#Info.ID = ReadByte(bstream) 
	#Info.Parent = ReadByte(bstream )
	#Info.Child = ReadByte(bstream )
	Info.rx = ReadFloat(bstream )
	Info.ry = ReadFloat(bstream)
	Info.rz = ReadFloat(bstream)
	Info.scale = ReadFloat(bstream)	   
	Info.Trans = [(ReadFloat (bstream)),(ReadFloat (bstream)),(ReadFloat (bstream))]
	return Info

class md5_bone:
	bone_index = 0
	name = ""
	bindpos = []
	bindmat = []
	origmat = []
	head = []
	tail = []
	scale = []
	parent = ""
	parent_index = 0
	blenderbone = None
	roll = 0

	def __init__(self):
		self.bone_index = 0
		self.name = ""
		self.bindpos = [0.0] * 3
		self.scale = [0.0] * 3
		self.head = [0.0] * 3
		self.tail = [0.0] * 3
		self.bindmat = [None] * 3  # is this how you initialize a 2d-array
		for i in range(3):
			self.bindmat[i] = [0.0] * 3
		self.origmat = [None] * 3  #is this how you initialize a 2d-array
		for i in range(3):
			self.origmat[i] = [0.0] * 3
		self.parent = ""
		self.parent_index = 0
		self.blenderbone = None

	def dump(self):
		print ("bone index: ", self.bone_index)
		print ("name: ", self.name)
		print ("bind position: ", self.bindpos)
		print ("bind translation matrix: ", self.bindmat)
		print ("parent: ", self.parent)
		print ("parent index: ", self.parent_index)
		print ("blenderbone: ", self.blenderbone)	 
		
class Header:
	BoneCount = 0 #,		--骨骼数
	MeshCount = 0 #,		--Mesh数
	MatCount = 0 #,		--材质数
	VertCount = 0 #,		--顶点数
	TriangleCount = 0 #,		--面数/3
	VertexIds = 0 #,		
	VertexBufferSize = 0#,		
	Padding = 0 #,		-- 0
	BoneMapCount = 0 #, 
	ptr_Bone = None #,
	ptr_BoneMap = None #,
	ptr_MatID = None #,
	ptr_Mesh = None #,		--Mesh地址
	ptr_vertex = None #,		--顶点地址
	ptr_triangle = None #,
	EndSize = 0

def ReadHeader(bstream):
	H = Header
	H.BoneCount		  = ReadShort(bstream)
	H.MeshCount		  = ReadShort(bstream)
	H.MatCount		  = ReadShort(bstream)
	H.VertCount		  = ReadLong(bstream)
	H.TriangleCount	  = ReadLong(bstream)
	H.VertexIds		  = ReadLong(bstream)
	H.VertexBufferSize	 = ReadLong(bstream)
	H.Padding			 = ReadLong(bstream)
	H.BoneMapCount		 = ReadLong(bstream)
	H.ptr_Bone		 = ReadLong(bstream)
	H.ptr_BoneMap	  = ReadLong(bstream)
	H.ptr_MatID	  = ReadLong(bstream)
	H.ptr_Mesh		  = ReadLong(bstream)
	H.ptr_vertex	  = ReadLong(bstream)
	H.ptr_triangle	  = ReadLong(bstream)
	H.EndSize	  = ReadLong(bstream)
	return H
	
class MeshHeader:
	unk01=0
	unk02 =0 
	faceOffset = 0
	faceCount = 0
	vertStart = 0
	vertCount = 0
	
	
	
	
def ReadMeshHeader( bstream ): 
	M = MeshHeader ()
	M.unk01 = ReadShort (bstream) #unsigned		--
	M.unk02 = ReadShort (bstream) #unsigned		--
	M.faceStart = ReadLong (bstream) #unsigned	
	M.faceCount = ReadShort (bstream) #unsigned
	return M	

	
def ReadFace (bstream):
	return [ReadShort (bstream),ReadShort (bstream),ReadShort (bstream)]	
	
def ReadFloat16 (fstream):
	hf=ReadShort(fstream) #unsigned
	exponent = ((hf & 0x7C00) >> 10) - 16
	fraction = hf & 0x03FF
	sign =	( hf >> 15 ) & 0x0001	# 16th bits
	if sign != 0:
		sign = 1 
	else:
		sign = 0	
	exponentF = exponent + 127
	outputAsFloat = (( fraction << 13) | \
	(exponentF << 23)) | (sign << 31)
	return (unpack('f',pack('I',outputAsFloat))[0])*2.0

def Float16 (hf):
	exponent = ((hf & 0x7C00) >> 10) - 16
	fraction = hf & 0x03FF
	sign =	( hf >> 15 ) & 0x0001	# 16th bits
	if sign != 0:
		sign = 1 
	else:
		sign = 0	
	exponentF = exponent + 127
	outputAsFloat = (( fraction << 13) | \
	(exponentF << 23)) | (sign << 31)
	return (unpack('f',pack('I',outputAsFloat))[0])*2.0	   
def FShort (fValue):
	Src = unpack('I',pack('f',fValue))[0]
	Sign=exponent=Mantissa=0
	Sign = (Src >> 31)
	exponent = (( Src & 0x7F800000) >>23) - 127 + 15
	Mantissa = Src & 0x007FFFFF
	if (exponent >= 0) and (exponent <= 30):
		Result = (Sign << 15) | ( (exponent << 10) |\
		( (Mantissa + 0x00001000) >>13))	
	else:
		if Src == 0:
			Result = 0
		else:
			if exponent <= 0:
				if exponent <= -10:
					Result = 0
				else:
					Mantissa = (Mantissa | 0x00800000) >> (1 - exponent)
					if (Mantissa | 0x00001000) >= 0:					
						Mantissa = Mantissa + 0x00002000
						Result = (Sign << 15)|(Mantissa >>13)
			else:
				if exponent == 255 - 127 + 15:				
					if Mantissa == 0:
						Result = (Sign << 15) | 0x7C00
					else:
						Result = (Sign<< 15) | ( 0x7C00 |( Mantissa >>13))
				else:
					if (Mantissa & 0x00001000) >= 0:
						Mantissa = Mantissa + 0x00002000
						if ( Mantissa & 0x00800000) >= 0:						
							Mantissa = 0
							exponent = exponent + 1											
					if exponent >= 30:					
						Result = (Sign << 15) | 0x7C00					
					else:					
						Result =(Sign <<15) |((exponent <<10) |(Mantissa >>13))
	return Result
	
def cross (a,b):
	return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
 
def getheadpos(pbone,bones):
	pos_head = [0.0] * 3

	#pos = mathutils.Vector((x,y,z)) * pbone.origmat
	pos = pbone.bindmat.to_translation()

	pos_head[0] = pos.x
	pos_head[1] = pos.y
	pos_head[2] = pos.z

	return pos_head

def gettailpos(pbone,bones):
	pos_tail = [0.0] * 3
	ischildfound = False
	childbone = None
	childbonelist = []
	for bone in bones:
		if bone.parent.name == pbone.name:
			ischildfound = True
			childbone = bone
			childbonelist.append(bone)
			
	if ischildfound:
		tmp_head = [0.0] * 3
		for bone in childbonelist:
			tmp_head[0] += bone.head[0]
			tmp_head[1] += bone.head[1]
			tmp_head[2] += bone.head[2]
		tmp_head[0] /= len(childbonelist)
		tmp_head[1] /= len(childbonelist)
		tmp_head[2] /= len(childbonelist)
		return tmp_head
	else:
		tmp_len = 0.5

		pos_tail[0] = pbone.head[0] #+ tmp_len * pbone.bindmat[0][0]
		pos_tail[1] = pbone.head[1] + tmp_len * -1.0; #pbone.bindmat[1][0]
		pos_tail[2] = pbone.head[2] #+ tmp_len * pbone.bindmat[2][0]

	return pos_tail
	
def create_dummy(name):
	bpy.ops.object.add(type='EMPTY')
	ob = bpy.context.object
	ob.name =  name	  
	ob.hide = True	  
	return ob
	"""
	def buildMesh( meshInfo, meshIndex, uiOffsetMeshGroupInfo, uiOffsetBoneMap, uiOffsetFaceData, usNumBones):
	"""
	
def modimport(infile):
	global DEBUGLOG

	print ("--------------------------------------------------")
	print ("---------SCRIPT EXECUTING PYTHON IMPORTER---------")
	print ("--------------------------------------------------")
	print ("Importing file: ", infile)

	SEEK_CUR = 1
	SEEK_SET = 0
	SEEK_END = 2
	f = open(infile,'rb')
	if (DEBUGLOG):
		logpath = infile.replace(".mesh", ".txt")
		print("logpath:",logpath)
		logf = open(logpath,'w')

	def printlog(strdata):
		if (DEBUGLOG):
			logf.write(strdata)

	objName = infile.split('\\')[-1].split('.')[0]

	me_ob = bpy.data.meshes.new(objName)
	print("objName:",objName)
	printlog(("New Mesh = " + me_ob.name + "\n"))

	MeshScale = (1.0,1.0,1.0)
	numOffsets = ReadLong(f)
	f.seek(0x10, SEEK_SET)
	numOffsets2 = ReadLong(f)
	f.seek(0x18, SEEK_SET)
	offsetMeshStart = ReadLong(f)
	f.seek(0x28, SEEK_SET)
	offsetMatInfo = ReadLong(f)
	f.seek(((numOffsets * 0x8) + 0x4),SEEK_SET)
	offsetBoneInfo = ReadLong(f)
	offsetBoneInfo2 = ReadLong(f)
	f.seek(((0x14 + numOffsets * 0x8) + numOffsets2 * 0x4), SEEK_SET)
	offsetStart = f.tell()
	f.seek(offsetStart + offsetMatInfo, SEEK_SET)
	uiNumMat = ReadLong(f)
	matInfo = []
	for i in range(uiNumMat):			
		matInfo.append( ReadLong(f))
		if (DEBUGLOG):
			print("Material hash: " + hex(matInfo[i]))	  
	
	f.seek(offsetStart + offsetMeshStart, SEEK_SET)
	uiMagic = ReadLong(f)
	uiUnk00 = ReadLong(f)
	uiMeshFileSize = ReadLong(f)
	uiUnk01 = ReadLong(f)
	
	f.seek(0x60, SEEK_CUR)#AABB MIN/MAX?
	
	uiUnk02 = ReadLong(f)
	uiOffsetMeshGroupInfo = ReadLong(f)
	uiOffsetMeshInfo = ReadLong(f)
	uiOffsetBoneMap = ReadLong(f)
	
	uiOffsetBoneMap = ReadLong(f)
	uiOffsetFaceData = ReadLong(f)
	usNumMeshGroups = ReadShort(f)
	usNumMesh = ReadShort(f)
	usNumBones = ReadShort(f)

	print("offsetStart "+hex(offsetStart ))		
	print("offsetMeshStart "+hex(offsetMeshStart ))	
	print("offsetBoneInfo "+hex(offsetBoneInfo ))	
	print("offsetBoneInfo2 "+hex(offsetBoneInfo2 ))	
	
	print("uiMagic "+hex(uiMagic ))	
	print("uiUnk00 "+hex(uiUnk00 ))	
	print("uiMeshFileSize "+hex(uiMeshFileSize ))	
	print("uiUnk01 "+hex(uiUnk01 ))	
	print("uiUnk02 "+hex(uiUnk02 ))
	print("uiOffsetMeshGroupInfo "+hex(uiOffsetMeshGroupInfo ))
	print("uiOffsetMeshInfo "+hex(uiOffsetMeshInfo ))
	print("uiOffsetBoneMap "+hex(uiOffsetBoneMap ))
	print("uiOffsetFaceData "+hex(uiOffsetFaceData ))
	print("usNumMeshGroups "+hex(usNumMeshGroups ))
	print("usNumMesh "+hex(usNumMesh ))
	print("usNumBones "+hex(usNumBones ))
	
#	 for i in range(1, bCount)
#		 bInfo = ReadBoneInfo(f)
#		 cBone = Dummy
#
	##
	#================================================================================================== 
	# Bones (Armature)
	#================================================================================================== 
	
	f.seek(offsetStart + offsetBoneInfo - 0x4, SEEK_SET)
	
	uiNumBones = ReadLong(f)
	f.seek(0xC, SEEK_CUR)
	f.seek(offsetStart + offsetBoneInfo2, SEEK_SET)
	#hdr.BoneCount = uiNumBones	   
	
	Bns = []
	bone = []

	md5_bones = []
	bni_dict = {}
	bInfo = []
	#================================================================================================== 
	# Bone Data 
	#==================================================================================================
	counter = 0
	# read bone info
	print ("uiNumBones =", uiNumBones)
	while counter < uiNumBones:
		#bInfo = ReadBoneInfo(f)
		#print("bone trans ", str(bInfo.Trans))
		#bone.append(bInfo[counter])
		f.seek(0x20, SEEK_CUR)
		fBoneXPos = ReadFloat(f)
		fBoneYPos = ReadFloat(f)
		fBoneZPos = ReadFloat(f)
		f.seek(0xC, SEEK_CUR)
		iBonePID = ReadLong(f)
		f.seek(0x4, SEEK_CUR)
		createbone = md5_bone()
		if debug:
			print ("bone "+str(counter)+" pid "+hex(iBonePID))
		if iBonePID == 0xffffffff:
			iBonePID = 0
		createbone.name = "b_" + str(iBonePID) + "_" + str(counter) #temp_name
		createbone.bone_index = counter
		if counter > 0:
			createbone.parent_index = iBonePID
		else:
			createbone.parent_index = 0
			
		createbone.bindpos[0] = fBoneXPos #bInfo[counter].Trans[0]
		createbone.bindpos[1] = fBoneYPos #bInfo[counter].Trans[1]
		createbone.bindpos[2] = fBoneZPos #bInfo[counter].Trans[2]
		createbone.scale[0] = 0.0
		createbone.scale[1] = 0.0
		createbone.scale[2] = 0.0

		bni_dict[createbone.name] = createbone.bone_index

		#w,x,y,z

		createbone.bindmat = mathutils.Quaternion((1,0,0,0)).to_matrix()
		createbone.bindmat = mathutils.Matrix.Translation(mathutils.Vector((fBoneXPos,fBoneYPos, fBoneZPos))) * \
							 createbone.bindmat.to_4x4()
		#createbone.bindmat = mathutils.Matrix.Translation(mathutils.Vector((bInfo[counter].Trans[0],-bInfo[counter].Trans[1], bInfo[counter].Trans[2]))) * \
		#					  createbone.bindmat.to_4x4()
		
		md5_bones.append(createbone)
		counter = counter + 1
		bnstr = createbone.name #(str(indata[0]))
		Bns.append(bnstr)

	for pbone in md5_bones:
		pbone.parent = md5_bones[pbone.parent_index]
	
	for pbone in md5_bones:
		if pbone.name != pbone.parent.name:
			pbone.bindmat = pbone.parent.bindmat * pbone.bindmat 
			#print(pbone.name)
			#print(pbone.bindmat)
			#print("end")
		else:
			pbone.bindmat = pbone.bindmat
		
	for pbone in md5_bones:
		pbone.head = getheadpos(pbone, md5_bones)

	for pbone in md5_bones:
		pbone.tail = gettailpos(pbone, md5_bones)

	for pbone in md5_bones:
		pbone.parent =	md5_bones[pbone.parent_index].name
  
	print ("-------------------------")
	print ("----Creating--Armature---")
	print ("-------------------------")

	#================================================================================================
	#Check armature if exist if so create or update or remove all and addnew bone
	#================================================================================================
	#bpy.ops.object.mode_set(mode='OBJECT')
	meshname ="ArmObject"
	objectname = "armaturedata"
	# arm = None  # UNUSED

	obj = bpy.data.objects.get(meshname)
	# arm = obj	 # UNUSED

	if obj:
		bpy.ops.error.message('INVOKE_DEFAULT', 
			type = "Error",
			message = 'Please start a new project before import.')
		f.close()
		return		
	else:
		armdata = bpy.data.armatures.new(objectname)
		ob_new = bpy.data.objects.new(meshname, armdata)
		#ob_new = bpy.data.objects.new(meshname, 'ARMATURE')
		#ob_new.data = armdata
		bpy.context.scene.objects.link(ob_new)
		#bpy.ops.object.mode_set(mode='OBJECT')
		for i in bpy.context.scene.objects:
			i.select = False #deselect all objects
		ob_new.select = True
		#set current armature to edit the bone
		bpy.context.scene.objects.active = ob_new
		#set mode to able to edit the bone
		if bpy.ops.object.mode_set.poll():
			bpy.ops.object.mode_set(mode='EDIT')

		#newbone = ob_new.data.edit_bones.new('test')
		#newbone.tail.y = 1
		print("creating bone(s)")
		bpy.ops.object.mode_set(mode='OBJECT')
		for bone in md5_bones:
			#print(dir(bone))
			bpy.ops.object.mode_set(mode='EDIT')#Go to edit mode for the bones
			newbone = ob_new.data.edit_bones.new(bone.name)
			#parent the bone
			#print("DRI:", dir(newbone))
			parentbone = None
			#note bone location is set in the real space or global not local
			#bonesize = bpy.types.Scene.unrealbonesize
			if bone.name != bone.parent:
				pos_x = bone.bindpos[0]
				pos_y = bone.bindpos[1]
				pos_z = bone.bindpos[2]
				#print("LINKING:" , bone.parent ,"j")
				parentbone = ob_new.data.edit_bones[bone.parent]
				newbone.parent = parentbone
				rotmatrix = bone.bindmat
				newbone.head.x = bone.head[0]
				newbone.head.y = bone.head[1]
				newbone.head.z = bone.head[2]
				newbone.tail.x = bone.tail[0]
				newbone.tail.y = bone.tail[1]
				newbone.tail.z = bone.tail[2]

				vecp = parentbone.tail - parentbone.head
				vecc = newbone.tail - newbone.head
				vecc.normalize()
				vecp.normalize()
				if vecp.dot(vecc) > -0.8:
					newbone.roll = parentbone.roll
				else:
					newbone.roll = - parentbone.roll
			else:
				rotmatrix = bone.bindmat
				newbone.head.x = bone.head[0]
				newbone.head.y = bone.head[1]
				newbone.head.z = bone.head[2]
				newbone.tail.x = bone.tail[0]
				newbone.tail.y = bone.tail[1]
				newbone.tail.z = bone.tail[2]
				newbone.roll = math.radians(90.0)

	bpy.context.scene.update()
	
	MeshVertex_array = [None] * usNumMesh	
	
	meshGroupIdx = 0
	print ("OffsetStart ",hex(offsetStart),"offsetMEshStart",hex(offsetMeshStart),"offsetMeshInfo",hex(uiOffsetMeshInfo))
	print ("MeshGroupInfo", hex(uiOffsetMeshGroupInfo),"MeshFaceData",hex(uiOffsetFaceData))
	print ("MeshStart", hex(offsetStart + offsetMeshStart ))
	print ("MeshInfoStart",hex(offsetStart + offsetMeshStart + uiOffsetMeshInfo))
	print ("MeshGroupInfo",hex(offsetStart + offsetMeshStart + uiOffsetMeshGroupInfo ))
	print ("FaceData",hex(offsetStart + offsetMeshStart + uiOffsetFaceData))
	for meshIndex in range(usNumMesh):
		f.seek(offsetStart + offsetMeshStart + uiOffsetMeshInfo + meshIndex * 0x30, SEEK_SET)
		if debug:
			print("Mesh Info Start: " + str(f.tell()))
		#buildMesh(self, f.read("1i2h10i"), i, uiOffsetMeshGroupInfo, uiOffsetBoneMap, uiOffsetFaceData, usNumBones)
		
		meshInfo = unpack('1i2h10i',f.read(48))
		print ("meshInfo ",meshInfo)
	   
		f.seek(offsetStart + offsetMeshStart + meshInfo[8] + 0x8, SEEK_SET)
		usNumVertexComponents = ReadShort(f)
		ucMeshVertStride = ReadByte(f)
		f.seek(0x5, SEEK_CUR)

		iMeshVertPos = -1
		iMeshNrmPos = -1
		iMeshTessNrmPos = -1
		iMeshTangPos = -1
		iMeshBiNrmPos = -1
		iMeshPckNTBPos = -1
		iMeshBwPos = -1
		iMeshBiPos = -1
		iMeshCol1Pos = -1
		iMeshCol2Pos = -1
		iMeshUV1Pos = -1
		iMeshUV2Pos = -1
		iMeshUV3Pos = -1
		iMeshUV4Pos = -1
		iMeshIIDPos = -1

		for i in range(usNumVertexComponents):
			uiEntryHash = ReadLong(f)
			usEntryValue = ReadShort(f)
			ucEntryType = ReadByte(f)
			ucEntryNull = ReadByte(f)
			
			if uiEntryHash == 0xD2F7D823:#Position
				iMeshVertPos = usEntryValue
				print("***iMeshVertPos")
			elif uiEntryHash == 0x36F5E414:#Normal
				iMeshNrmPos = usEntryValue
				print("***iMeshNrmPos")
			elif uiEntryHash == 0x3E7F6149:#TessellationNormal
				if debug:
					print("Unsupported Vertex Component: TessellationNormal! " + "Pos: " + str(usEntryValue))
			#	iMeshTessNrmPos = usEntryValue
			elif uiEntryHash == 0xF1ED11C3:#Tangent
				iMeshTangPos = usEntryValue
				print("***iMeshTangPos")
			elif uiEntryHash == 0x64A86F01:#Binormal
				if debug:
					print("Unsupported Vertex Component: BiNormal! " + "Pos: " + str(usEntryValue))
			#	iMeshBiNrmPos = usEntryValue
			elif uiEntryHash == 0x9B1D4EA:#PackedNTB
				if debug:
					print("Unsupported Vertex Component: PackedNTB! " + "Pos: " + str(usEntryValue))
			#	iMeshPckNTBPos = usEntryValue
			elif uiEntryHash == 0x48E691C0:#SkinWeights
				iMeshBwPos = usEntryValue
				print("***iMeshBwPos")
			elif uiEntryHash == 0x5156D8D3:#SkinIndices
				iMeshBiPos = usEntryValue
				print("***iMeshBiPos")
			elif uiEntryHash == 0x7E7DD623:#Color1
				iMeshCol1Pos = usEntryValue				
				if debug:
					print("Unsupported Vertex Component: Color1! " + "Pos: " + str(usEntryValue))
			elif uiEntryHash == 0x733EF0FA:#Color2
				if debug:
					print("Unsupported Vertex Component: Color2! " + "Pos: " + str(usEntryValue))
			#	iMeshCol2Pos = usEntryValue
			elif uiEntryHash == 0x8317902A:#Texcoord1
				iMeshUV1Pos = usEntryValue
				print("***iMeshUV1Pos")
			elif uiEntryHash == 0x8E54B6F3:#Texcoord2
				iMeshUV2Pos = usEntryValue
				print("***iMeshUV2Pos")
			elif uiEntryHash == 0x8A95AB44:#Texcoord3
				if debug:
					print("Unsupported Vertex Component: Texcoord3! " + "Pos: " + str(usEntryValue))
			#	iMeshUV3Pos = usEntryValue
			elif uiEntryHash == 0x94D2FB41:#Texcoord4
				if debug:
					print("Unsupported Vertex Component: Texcoord4! " + "Pos: " + str(usEntryValue))
			#	iMeshUV4Pos = usEntryValue
			elif uiEntryHash == 0xE7623ECF:#InstanceID
				if debug:
					print("Unsupported Vertex Component: InstanceID! " + "Pos: " + str(usEntryValue))
				iMeshUV2Pos = usEntryValue
			else:
				if debug:
					print("Unknown Vertex Component! Hash: " + str(hex((uiEntryHash))) + " value: " + str(usEntryValue))
				
		if meshInfo[2] != 0 and bSkinningEnabled != 0:
			f.seek(offsetStart + offsetMeshStart + meshInfo[3], SEEK_SET)
			boneMap = []
			for i in range(meshInfo[2]):
				boneMap.append(ReadLong(f))
			print ("bone map [",meshInfo[2],"] ",boneMap)		
			#rapi.rpgSetBoneMap(boneMap)
			
		#print(" vert count "+str(meshInfo[9]))
		f.seek(offsetStart + offsetMeshStart + meshInfo[4], SEEK_SET)
		vertBuff = f.read(meshInfo[9] * ucMeshVertStride)			 
		
		Vert_array = [None] * meshInfo[9]
		vc = meshInfo[9]
		VertexPos_array = [None] * vc
		#VertexPos_array.count = vc
		UV_array = [None] * vc
		#UV_array.count = vc
		BoneID_array = [None] * vc
		#BoneID_array.count = vc
		BoneWeight_array = [None] * vc
		#BoneWeight_array.count = vc
		
		if iMeshVertPos != -1:			  
			#rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, ucMeshVertStride, iMeshVertPos)
			vertStart = iMeshVertPos
			for v in range(meshInfo[9]):					
				Vert_array[v]=unpack('3f',vertBuff[vertStart:(vertStart+0xC)])					  
				#posz = float((vertBuff[idx]) )
				#posy = float((vertBuff[idx + 4]) )
				#posx = float((vertBuff[idx + 8]) )					   
				vertStart+= ucMeshVertStride
		#print("VertArray ",Vert_array)				
		for i in range(meshInfo[0]):
			print ("mesh ", i)			 
			f.seek(offsetStart + offsetMeshStart + uiOffsetMeshGroupInfo + meshGroupIdx * 0x50, SEEK_SET)
			meshGroupIdx += 1
			meshGroupInfo = unpack("iiiiiiiiiiiiiiiiiiii",f.read(80))
			print ("GroupIdx ", meshGroupIdx, "GroupInfo ", hex(meshGroupInfo[0]),hex(meshGroupInfo[1]),hex(meshGroupInfo[2]),hex(meshGroupInfo[3]),hex(meshGroupInfo[4]),hex(meshGroupInfo[5]))
			#rapi.rpgSetName("Mesh_" + str(meshIndex) + "_" + str(i))
			#rapi.rpgSetPosScaleBias((fDefaultMeshScale, fDefaultMeshScale, fDefaultMeshScale), (0, 0, 0))
			
			f.seek(offsetStart + offsetMeshStart + uiOffsetFaceData + meshGroupInfo[4] * 0x2, SEEK_SET)
			#faceBuff = f.read(meshGroupInfo[5] * 0x6)
			Face_array = [None] * meshGroupInfo[5]
			#print(" face count "+str(meshGroupInfo[5]))
			idxList = []
			if meshGroupInfo[5] > 0:
				for c in range(meshGroupInfo[5]):			 
					i1 = ReadShort(f)
					i2 = ReadShort(f) 
					i3 = ReadShort(f)				 
					Face_array[c] = [i1, i2, i3, 0] 
					idxList.append (i1)
					idxList.append (i2)
					idxList.append (i3);
					#print ("face " +str(c) ,Face_array[c])	
				idxList.sort()
				vstart = idxList[0]	   # first vertex index used
				vend = idxList[-1]+1   # last index used
				vc = vend - vstart

			else:
				vstart = 0 
				vend = 1
				vc = 0
			#print ("vstart vend vc ",vstart, vend, vc)
			for c in range(meshGroupInfo[5]):			 
				i1 = Face_array[c][0]
				i2 = Face_array[c][1]
				i3 = Face_array[c][2]
				Face_array[c] = [i1-vstart, i2-vstart, i3-vstart, 0]				 
										  
			#rapi.rpgSetUVScaleBias(NoeVec3 ((16.0, 16.0, 16.0)), NoeVec3 ((16.0, 16.0, 16.0)))
			#rapi.rpgSetTransform(NoeMat43((NoeVec3((1, 0, 0)), NoeVec3((0, 0, 1)), NoeVec3((0, -1, 0)), NoeVec3((0, 0, 0)))))
			
			Norm_array =  [None] * meshInfo[9]
			if iMeshNrmPos != -1 and bNORMsEnabled != 0: #PC, convert normals. Thanks to Dunsan from UnpackTRU just a custom version
				normList = []
				for n in range(meshInfo[9]):
					idx = ucMeshVertStride * n + iMeshNrmPos
					nz = float((vertBuff[idx]) / 255.0 * 2 - 1)
					ny = float((vertBuff[idx + 1]) / 255.0 * 2 - 1)
					nx = float((vertBuff[idx + 2]) / 255.0 * 2 - 1)
					l = math.sqrt(nx * nx + ny * ny + nz * nz)
					normList.append(nx / l)
					normList.append(ny / l)
					normList.append(nz / l)
					Norm_array[n] = [nx / l, ny / l , nz / l]
				#normBuff = struct.pack("<" + 'f'*len(normList), *normList)
				#rapi.rpgBindNormalBufferOfs(normBuff, noesis.RPGEODATA_FLOAT, 0xC, 0x0)
			#if iMeshTessNrmPos != -1:
			#	print("Unsupported")
			#if iMeshTangPos != -1:
			#	 rapi.rpgBindTangentBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, ucMeshVertStride, iMeshTangPos, 0x4)
			#if iMeshBiNrmPos != -1:
			#	print("Unsupported")
			#if iMeshPckNTBPos != -1:
			#	print("Unsupported")
			BoneWeight_array = []
			if iMeshBwPos != -1 and bSkinningEnabled != 0:				  
				for w in range(vstart,vend):
					idx = ucMeshVertStride * w + iMeshBwPos
					BoneWeight_array.append([float((vertBuff[idx]) / 255.0),
					float((vertBuff[idx + 1]) / 255.0),
					float((vertBuff[idx + 2]) / 255.0),
					float((vertBuff[idx + 3]) / 255.0)])
				#weightBuff = pack("<" + 'f'*len(weightList), *weightList)
				#rapi.rpgBindBoneWeightBufferOfs(weightBuff, noesis.RPGEODATA_FLOAT, 0x10, 0x0, 0x4)
			BoneID_array = []
			if iMeshBiPos != -1 and bSkinningEnabled != 0:
				print ("Bone index found")
				for bi in range(vstart,vend):
					idx = ucMeshVertStride * bi + iMeshBiPos
					BoneID_array.append([boneMap[vertBuff[idx]],
							boneMap[vertBuff[idx + 1]], 
							boneMap[vertBuff[idx + 2]],
							boneMap[vertBuff[idx + 3]]])
				#rapi.rpgBindBoneIndexBufferOfs(vertBuff, noesis.RPGEODATA_UBYTE, ucMeshVertStride, iMeshBiPos, 0x4)	
			Col1_array = []
			if iMeshCol1Pos != -1 and bCOLsEnabled != 0:
			#	 rapi.rpgBindColorBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, ucMeshVertStride, iMeshCol1Pos, 0x4)	
				for w in range(vstart,vend):
					idx = ucMeshVertStride * w + iMeshBwPos
					Col1_array.append([float((vertBuff[idx]) / 255.0),
					float((vertBuff[idx + 1]) / 255.0),
					float((vertBuff[idx + 2]) / 255.0),
					float((vertBuff[idx + 3]) / 255.0)])				 
			#if iMeshCol2Pos != -1:
			#	print("Unsupported")
			MeshUV_array = []
			if iMeshUV1Pos != -1 and bUVsEnabled != 0:
				#rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_SHORT, ucMeshVertStride, iMeshUV1Pos)
				for w in range(vstart,vend):
					idx = ucMeshVertStride * w + iMeshUV1Pos
					MeshUV_array.append( [(unpack('<h',vertBuff[idx:(idx+2)])[0]/2048.0),1.0-(unpack('<h',vertBuff[(idx+2):(idx+4)])[0]/2048.0),0.0])
					#print (" UV "+str(float(unpack('1H',vertBuff[idx:(idx+2)])[0]/2048.0))+" "+str(float(unpack('1H',vertBuff[(idx+2):(idx+4)])[0]/2048.0)))
					 
			#if iMeshUV2Pos != -1 and bUVsEnabled != 0:
			#	 rapi.rpgBindUV2BufferOfs(vertBuff, noesis.RPGEODATA_SHORT, ucMeshVertStride, iMeshUV2Pos)
			#if iMeshUV3Pos != -1:
			#	print("Unsupported")
			#if iMeshUV4Pos != -1:
			#	print("Unsupported")
			#if iMeshIIDPos != -1:
			#	print("Unsupported")
			#if bRenderAsPoints:
			#	 rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, meshInfo[16], noesis.RPGEO_POINTS, 0x1)
			#else:
			#	 rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, int(meshGroupInfo[5] * 0x3), noesis.RPGEO_TRIANGLE, 0x1)
			#if bOptimizeMesh:
			#	 rapi.rpgOptimize()
			#rapi.rpgClearBufferBinds()
			print ("GroupIdx ", meshGroupIdx, "GroupInfo ", hex(meshGroupInfo[0]),hex(meshGroupInfo[1]),hex(meshGroupInfo[2]),hex(meshGroupInfo[3]),hex(meshGroupInfo[4]),hex(meshGroupInfo[5]))
			
			print ("Mi", meshIndex, " i ",i,"gi6 " ,meshGroupInfo[7], " gi7 ",meshGroupInfo[7], " gi14 ",meshGroupInfo[14], "_mat table size ",len(matInfo));
			objName = "Mesh_" + str(meshIndex) + "_" + str(i) + "_Flag" + hex(meshGroupInfo[7]) + "_Mat" + hex(matInfo[meshGroupInfo[14]])	+ "_s"+ str(vstart)+ "_e"+ str(vend-1)	#"Mesh_"+ ("%03d" % i) #+"_"
			me_ob = bpy.data.meshes.new(objName)
			print("objName:",objName)
			
			#================================================================================================== 
			#Building Mesh
			#================================================================================================== 
			
			fc = meshGroupInfo[5]
			
			#print("vertex:", vc, "faces:", fc)
			#print("vertex2:", vc)
			
			me_ob.vertices.add(vc)
			me_ob.tessfaces.add(fc)
			me_ob.vertices.foreach_set("co", unpack_list( Vert_array[vstart:vend]))
			me_ob.tessfaces.foreach_set("vertices_raw", unpack_list( Face_array))
			bpy.ops.object.mode_set(mode='OBJECT')			  
			
			# Col1 map
			if len(Col1_array) > 0:
				if me_ob.vertex_colors.find("Col1") == -1:
					me_ob.vertex_colors.new(name="Col1")					
				col1_map = me_ob.vertex_colors.get("Col1") 
				
				for poly in me_ob.polygons:
					for loop_index in  range(poly.loop_start, poly.loop_start + poly.loop_total):
						# cramp normal value [-1..1] into [ 0..1]
						#print	("vertex color = ",normal_cache.data[loop_index].color)
						col1_map.data[loop_index].color[0] = Col1_array[me.loops[loop_index].vertex_index][0]
						col1_map.data[loop_index].color[1] = Col1_array[me.loops[loop_index].vertex_index][1]
						col1_map.data[loop_index].color[2] = Col1_array[me.loops[loop_index].vertex_index][2]
						#print	("after vertex color = ",normal_cache.data[loop_index].color)
			
			# Try to use vertex color layer as custom normal cache
			'''
			if me_ob.vertex_colors.find("NormalCache") == -1:
				me_ob.vertex_colors.new(name="NormalCache")					   

			normal_cache = me_ob.vertex_colors.get("NormalCache")										 
			
			# cache normal 
			me_ob.calc_normals_split()			  
			for poly in me_ob.polygons:
				for loop_index in  range(poly.loop_start, poly.loop_start + poly.loop_total):
					# cramp normal value [-1..1] into [ 0..1]
					#print	("vertex color = ",normal_cache.data[loop_index].color)
					normal_cache.data[loop_index].color[0] = me_ob.loops[loop_index].normal[0]*0.5+0.5
					normal_cache.data[loop_index].color[1] = me_ob.loops[loop_index].normal[1]*0.5+0.5
					normal_cache.data[loop_index].color[2] = me_ob.loops[loop_index].normal[2]*0.5+0.5
					#print	("after vertex color = ",normal_cache.data[loop_index].color)					 
			me_ob.free_normals_split()
			'''
			# set up UV map		   
			if len(MeshUV_array) > 0: #[0] != None:
				me_ob.uv_textures.new(name="UVTex")
			
			#print("INIT UV TEXTURE...")
			_matcount = 0
			#for mattexcount in materials:
				#print("MATERAIL ID:", _matcount)
			_textcount = 0		  
			for uv in me_ob.tessface_uv_textures: # uv texture
				#print("UV TEXTURE ID:",_textcount)
				#print(dir(uv))
				for face in me_ob.tessfaces:# face, uv
					#print(dir(face))
	#				 if faceuv[face.index][1] == _textcount: #if face index and texture index matches assign it
					mfaceuv = Face_array[face.index] #face index
					#print (" i =", i, " mfaceuv[0] = " ,mfaceuv[0])
					_uv1 = MeshUV_array[mfaceuv[0]] #(0,0)
					uv.data[face.index].uv1 = mathutils.Vector((_uv1[0], _uv1[1])) #set them
					_uv2 = MeshUV_array[mfaceuv[1]] #(0,0)
					uv.data[face.index].uv2 = mathutils.Vector((_uv2[0], _uv2[1])) #set them
					_uv3 = MeshUV_array[mfaceuv[2]] #(0,0)
					uv.data[face.index].uv3 = mathutils.Vector((_uv3[0], _uv3[1])) #set them
					#print ("tessface vertices = ",face.vertices)
					#print ("tessface vertices_raw = ",face.vertices_raw)
				_textcount += 1
				#_matcount += 1
				#print(matcount)
			#print("END UV TEXTURE...")
		   
			
			#===================================================================================================
			#
			#===================================================================================================
			obmesh = bpy.data.objects.new(objName,me_ob)
			obmesh.scale = MeshScale
			obmesh.location = mathutils.Vector([0.0,0.0,0.0])
			
			#===================================================================================================
			#Mesh Vertex Group bone weight
			#===================================================================================================
			print("---- building bone weight mesh ----")
			#print(dir(ob_new.data.bones))
			#create bone vertex group #deal with bone id for index number
			for bone in ob_new.data.bones:
				#print("names:", bone.name, ":", dir(bone))
				group = obmesh.vertex_groups.new(bone.name)
				#print ("vgroup bone:", bone.name)
			
			for c in range (vc):
				#print ("BoneID_array", BoneID_array)
				if len(BoneID_array) > 0: #[0] != None:
					for j,boneIdx in enumerate(BoneID_array[c]):
						#print ("vertex id =" ,c, " boneIdx = ", boneIdx)					   
						vgroup = obmesh.vertex_groups.get(md5_bones[boneIdx].name)
						if vgroup:
							#print ("md5_bone = ", md5_bones[boneIdx].name)
							if len(BoneWeight_array) > 0:
								vgroup.add([c],BoneWeight_array[c][j], 'ADD')	
							else:
								vgroup.add([c],0.25, 'ADD')
				else:
					if len(obmesh.vertex_groups) >0:
						vgroup = obmesh.vertex_groups[0]
						if	vgroup:
							vgroup.add([c],0.0, 'ADD') 
								   
			#print("---- adding mesh to the scene ----")

			bpy.ops.object.mode_set(mode='OBJECT')
			#bpy.ops.object.select_pattern(extend=True, pattern=obmesh.name, case_sensitive=True)
			#bpy.ops.object.select_pattern(extend=True, pattern=ob_new.name, case_sensitive=True)

			#bpy.ops.object.select_name(name=str(obmesh.name))
			#bpy.ops.object.select_name(name=str(ob_new.name))
			#bpy.context.scene.objects.active = ob_new
			
			mod = obmesh.modifiers.new(type="ARMATURE", name="Armature")
			mod.use_vertex_groups = True
			mod.object = ob_new
			
			me_ob.update()

			bpy.context.scene.objects.link(obmesh)	 
			bpy.context.scene.update()
			obmesh.select = False
			ob_new.select = False
			obmesh.select = True
			ob_new.select = True

		if debug:
			print("Mesh Info End: " + str(f.tell()))	
	f.close()
'''		
def GetVertexBoneID(MeshObj, v, index ):	
	vgroup = None
	for	 vg in MeshObj.vertex_groups:
		if vg.index == v.groups[index].group:
			vgroup = vg
			break							 
	if vgroup != None:						   
		#print ("vgroup name :", vgroup.name)
		bone_id =  int(re.split('_',vgroup.name)[2])  #skinOps.GetVertexWeightBoneID theSkin c 1
		#print ("bone id = ", bone_id)
	else: 
		bone_id = 0
		print ("cannot find vertices group number ",  v.groups[index].group)
	return bone_id
'''
def GetVertexBoneID(VGroupLUT, v, index ):	  
	
	return VGroupLUT[v.groups[index].group]
	'''	
	vgroup = None
	if vgroup != None:						   
		#print ("vgroup name :", vgroup.name)
		bone_id =  int(re.split('_',vgroup.name)[2])  #skinOps.GetVertexWeightBoneID theSkin c 1
		#print ("bone id = ", bone_id)
	else: 
		bone_id = 0
		print ("cannot find vertices group number ",  v.groups[index].group)
	return bone_id
	''' 
#===========================================================================
# Main
#===========================================================================
def do_export(self, context, props, filepath, bSmoothOverlapVertex):
	SEEK_SET = 0
	SEEK_CUR = 1
	SEEK_END = 2
	print("Filepath: {}".format(filepath))
	selection = context.selected_objects		
	selcnt= len (selection)
	f = open(filepath,'rb')
	if f != None and selcnt != 0:
		file_size = f.seek(0, SEEK_END)
		f.seek(0,SEEK_SET)
		
		numOffsets = ReadLong(f)
		f.seek(0x10, SEEK_SET)
		numOffsets2 = ReadLong(f)
		f.seek(0x18, SEEK_SET)
		offsetMeshStart = ReadLong(f)
		f.seek(0x28, SEEK_SET)
		offsetMatInfo = ReadLong(f)
		f.seek(((numOffsets * 0x8) + 0x4),SEEK_SET)
		offsetBoneInfo = ReadLong(f)
		offsetBoneInfo2 = ReadLong(f)
		f.seek(((0x14 + numOffsets * 0x8) + numOffsets2 * 0x4), SEEK_SET)
		offsetStart = f.tell()
		
		
		f.seek(offsetStart + offsetMeshStart, SEEK_SET)
		uiMagic = ReadLong(f)
		uiUnk00 = ReadLong(f)
		OffsetMeshFileSize = f.tell()
		uiMeshFileSize = ReadLong(f)
		uiUnk01 = ReadLong(f)
		
		f.seek(0x60, SEEK_CUR)#AABB MIN/MAX?
		
		uiUnk02 = ReadLong(f)
		GroupInfoHeaderOffset=f.tell()
		uiOffsetMeshGroupInfo = ReadLong(f)
		uiOffsetMeshInfo = ReadLong(f)
		BoneMapHeaderOffset=f.tell();		
		uiOffsetBoneMap = ReadLong(f)		
		uiOffsetBoneMap2 = ReadLong(f)		
		# does this mesh have bone map?
		if (uiOffsetMeshInfo == uiOffsetBoneMap):
			bHasBoneMap = False
		else:
			bHasBoneMap = True
		FaceDataHeaderOffset=f.tell()
		uiOffsetFaceData = ReadLong(f)
		numGroupHeader	= f.tell()
		usNumMeshGroups = ReadShort(f)
		usNumMesh = ReadShort(f)
		usNumBones = ReadShort(f)
		
		f.seek(0,SEEK_SET)
		
		# --建立新文件
		filename = filepath.split('.')[0]
		nf = open(filename +"_new.mesh",'wb')
		# aman: copy everything up to mesh info
		copyLen = offsetStart + offsetMeshStart + uiOffsetMeshInfo
		nLong = int(copyLen/4)
		remain = copyLen %4
		for i in range(nLong):
			temp = ReadLong(f)
			WriteLong(nf,temp)
		for i in range(remain):
			temp = ReadByte(f)
			WriteByte(nf,temp)		  
		
		#--Mesh Info 不修改没有改动的模型
		#selection = context.selected_objects		 
		#selcnt= len (selection)
		if selcnt == 0:
			f.close()
			nf.close()
		
		SelectMeshInfo = [None] * selcnt
		SelectMeshInfo2 = [None] * selcnt
		addMeshInfo = []
		
		usNumMeshTot = usNumMesh
		usNumAddMesh = 0
		for i in range(selcnt):
			#sName = filterString selection[i].name "_"
			sName = re.split('_',selection[i].name)
			#print("sName = ", sName)
			if (sName[0]=="xMesh"):
				usNumAddMesh = usNumAddMesh + 1
				usNumMeshTot=usNumMeshTot + 1
				addMeshInfo.append((selection[i],sName[1],sName[2],i))
			else:
				SelectMeshInfo[i] = (selection[i],sName[1],sName[2],i)		#--#(Mesh, MeshIndex, SubMeshInd)
			 
			#if len(sName) >= 7:
			#	 mshHdr_matid = int (re.split(':',sName[4])[1])
			#	 mshHdr_grp = int (re.split( ':', sName[5])[1])
			#	 mshHdr_mde = int (re.split( ':', sName[6])[1])
			#	 mshHdr_lod = int (re.split( 'x', sName[3])[1])
			#	 SelectMeshInfo2[i] = (mshHdr_matid,mshHdr_grp,mshHdr_mde,mshHdr_lod)
			#	 #print ("select2 =", SelectMeshInfo2[i])			 
			
		#--print SelectMeshInfo
		NewMeshInfo = [[None]*12] * usNumMeshTot
		MeshUV_array = [None] * usNumMeshTot
		MeshNorm_array = [None] * usNumMeshTot		  
		
		print(" offset ", f.tell(), " new offset ", nf.tell())
		faceOffset = 0
		total_face = 0		  
		
		meshGroupIdx = 0
		bmOffsetDiff = 0
		bmOffsetStart = 0
		MeshInfoArray = [None] * usNumMeshTot
		SaveInfoArray = [None] * usNumMeshTot
		BoneMapArray = [None] * usNumMeshTot
		OrigBoneMapArray = [None] * usNumMeshTot
		Bone_array = [None] * usNumMeshTot
		
		
		
		MeshChange =  [dict() for x in range(usNumMeshTot)] # array of dictionary
		NewGroupArray = [dict() for x in range(usNumMeshTot)]
		GroupVertArray = [dict() for x in range(usNumMeshTot)]
		GroupUVArray = [dict() for x in range(usNumMeshTot)]	 
		GroupNormArray = [dict() for x in range(usNumMeshTot)]
		GroupTanArray = [dict() for x in range(usNumMeshTot)]	  
		GroupBiNrmArray = [dict() for x in range(usNumMeshTot)]		
		VGroupLUT = [dict() for x in range(usNumMeshTot)]	  
		boneMapLen = [ 0 ] * usNumMeshTot
		
		totalMeshInfo =(usNumMesh + usNumAddMesh)* 0x30 
		alignedMeshInfo = (totalMeshInfo +31)&0xffffffe0
 
		extraMeshInfo= alignedMeshInfo-(usNumMesh*0x30)
		
		print(" numM newM totM	 aligedM extrM ",usNumMesh,usNumAddMesh,hex(totalMeshInfo),hex(alignedMeshInfo),hex(extraMeshInfo))
		
		for i in range(usNumMeshTot):
	   
			bMeshSame = False
			sc = 0
			
			if (i >= usNumMesh):
				addMeshIdx =  i - usNumMesh
				srcMeshInfoId= int(addMeshInfo[addMeshIdx][1])
				f.seek(offsetStart + offsetMeshStart + uiOffsetMeshInfo + srcMeshInfoId * 0x30, SEEK_SET)
			else:
				f.seek(offsetStart + offsetMeshStart + uiOffsetMeshInfo + i * 0x30, SEEK_SET)			
			meshInfo = list( unpack('1i2h10i',f.read(48)))
			if (i >=usNumMesh):
				meshInfo[0]=1
				meshInfo[9]=0
			SaveInfoArray[i] = list(meshInfo)
			MeshInfoArray[i] = list(meshInfo)
			
			f.seek(offsetStart + offsetMeshStart + meshInfo[8] + 0x8, SEEK_SET)			   
			boneMap = []	   
			if (i < usNumMesh):	 # normal processing
				if meshInfo[2] != 0:
					f.seek(offsetStart + offsetMeshStart + meshInfo[3], SEEK_SET)
					for j in range(meshInfo[2]):  
						boneMap.append(ReadLong(f))
					OrigBoneMapArray[i]=list(boneMap)
				
				for j in range(selcnt):
					if SelectMeshInfo[j] != None:
						ind = int( SelectMeshInfo[j][1] )  # Find out which mesh/group is selected as modified
						if ind == i:								
							bMeshSame = True 
							subidx =  int( SelectMeshInfo[j][2] )
							group_idx = meshGroupIdx
							if subidx < meshInfo[0]:	#submesh (group) count
									MeshChange[i][subidx]=j	 # remember select index
			else:
				bMeshSame = True  # a new added mesh
				MeshChange[i][0]=addMeshInfo[i-usNumMesh][3]
				
			if bMeshSame == True:	# This mesh is marked as modified
				#need bonemap, total vertex, vert_buf offset, component offset
				total_vc = 0
				max_vend = 0				
				reset = False
				last_vc = meshInfo[9]
				#new_end = last_vc
				new_end = 0
				print ("meshchange", i, MeshChange[i])
				for k in range(meshInfo[0]):  # check which group in mesh has changed
					if (i < usNumMesh):
						f.seek(offsetStart + offsetMeshStart + uiOffsetMeshGroupInfo + meshGroupIdx * 0x50, SEEK_SET)										 
						meshGroupInfo = unpack("iiiiiiiiiiiiiiiiiiii",f.read(80))	
					   
						vstart = 0
						vend = 0
						f.seek(offsetStart + offsetMeshStart + uiOffsetFaceData + meshGroupInfo[4] * 0x2, SEEK_SET)					   
						Face_array = [None] * meshGroupInfo[5]
						fc = meshGroupInfo[5]
						#print(" face count "+str(meshGroupInfo[5]))
						idxList = []
						for c in range(meshGroupInfo[5]):			 
							i1 = ReadShort(f)
							i2 = ReadShort(f) 
							i3 = ReadShort(f)				 
							Face_array[c] = [i1, i2, i3, 0] 
							idxList.append (i1)
							idxList.append (i2)
							idxList.append (i3);
							#print ("face " +str(c) ,Face_array[c])
						idxList.sort()
						vstart = idxList[0]	   # first vertex index used
						vend = idxList[-1]+1   # last index used	  
					else:
						vstart = 0
						vend = 1
					
					if k in MeshChange[i]:	#  this group need to be update						   
						sc = MeshChange[i][k]
						try:
							if i < usNumMesh:
								obj = SelectMeshInfo[sc][0]
							else:
								obj = addMeshInfo[i-usNumMesh][0]
							OutMesh = obj.to_mesh(context.scene, True, 'PREVIEW', calc_tessface=False)
						except RuntimeError:
							OutMesh = None

						if OutMesh is None:
							continue  
						vc = len(OutMesh.vertices)				   
						fc = len(OutMesh.polygons)
						
						MeshUV = {}	  # build vertex uv lookup dictionary
						for c in range(vc):
							MeshUV[c] = mathutils.Vector([0.0,0.0])
						if i < usNumMesh:	
							me = SelectMeshInfo[sc][0]
						else:
							me = addMeshInfo[i-usNumMesh][0]						
						uv_layer = OutMesh.uv_layers.active.data				
						for poly in OutMesh.polygons:						 
							for loop_index in range (poly.loop_start, poly.loop_start + poly.loop_total):
								MeshUV[OutMesh.loops[loop_index].vertex_index]=mathutils.Vector([uv_layer[loop_index].uv[0],1.0-uv_layer[loop_index].uv[1]])
						#print("Mesh UV = ",MeshUV)
						#for c in range(vc):   # convert to mk9 v coordinate
						#	 MeshUV[c].y = 1.0 - MeshUV[c].y
						GroupUVArray[i][k] = MeshUV
						
						NormArray = [None] * vc
						#NormArray.count = vc
						
						if OutMesh.vertices[0].normal == None:
							OutMesh.calc_normals()															  
							
						if bSmoothOverlapVertex:
							# aman: Blender calculates vertex normal from faces contain that vertex and creates hard edges between disjointed faces in mesh
							# Here is a hack to average vertex normals of overlapped vertex to remove the hard edges. This make all overlapped edges smooth
							# Real solution would be some day Blender supports editing of vertex normal.
																	   
							vertex_check_list = [[v.co, 0 , v.normal] for v in OutMesh.vertices]	 
							num_vert = len (vertex_check_list)
							
							for edge in OutMesh.edges:	  
								if edge.use_edge_sharp:	 # if an edge is marked as sharp edge
									vertex_check_list[edge.vertices[0]][1] = -1	 # exclude vertex pair from smoothing
									vertex_check_list[edge.vertices[1]][1] = -1	 # 
									# print (" Sharp edge = ",edge.vertices[0],edge.vertices[1])
							#print ("vertlist = ", vertex_check_list)
							print ("average duplicated vertex normals")
							for idx in	range (num_vert):
								#if OutMesh.vertices[idx].bevel_weight == -10.0:  # -10 means exclude this vertex from smoothing
								#	 print ("bevel_weight == -10")
								#	 continue
								v1 = vertex_check_list[idx]
								#print( "v1 = ", v1)
								if v1[1] == 0:	# vertex 
									overlap = [idx] 
									v1[1] = 1 
									for j in range( idx+1, num_vert):
										v2 =  vertex_check_list[j]
										if v2[1] == 0: # vertex overlap not found yet
											if v1[0] == v2[0]:
												 v1[1] = v1[1] + 1
												 v2[1] = -1 # mark vertex processed
												 overlap.append(j)
									if v1[1] > 1:	# found overlapped vertices
										#print("overlap = " , overlap)
										new_normal = mathutils.Vector([0.0,0.0,0.0])
										for v_index in overlap:
											new_normal.x += OutMesh.vertices[v_index].normal[0]
											new_normal.y += OutMesh.vertices[v_index].normal[1]
											new_normal.z += OutMesh.vertices[v_index].normal[2]
										new_normal *= (1.0/v1[1])  # average
										#new_normal.normalize()
										#print ("new normal = ", new_normal)
										for v_index in overlap:
											vertex_check_list[v_index][2] = new_normal										  
							for v in range(vc):
								N = vertex_check_list[v][2].normalized()
								NormArray[v] = mathutils.Vector([N.x,N.y,N.z])
								#print ("NormArray=", NormArray[v])
						else:
							print ("Use Blender vertex normals")																		   
							OutMesh.calc_normals_split()  # support custom normal created by edit normal/copy data modifier 
							for poly in OutMesh.polygons:						
								for loop_index in range (poly.loop_start, poly.loop_start + poly.loop_total):
									N = OutMesh.loops[loop_index].normal
									if N != None:
										NormArray[OutMesh.loops[loop_index].vertex_index]=mathutils.Vector([N.x,N.y,N.z])
							for v in range(vc): 
								if NormArray[v] == None: # for vertex that has no custom normal ,use Blender normal
									N = OutMesh.vertices[v].normal
									NormArray[v] = mathutils.Vector([N.x,N.y,N.z])						  

						GroupNormArray[i][k] = NormArray;
						#if theSkin != undefined then modPanel.setCurrentObject theSkin
														   
						b1=0;b2=0;b3=0;b4=0;b5=0;b6=0;w1=0.0;w2=0.0;w3=0.0;w4=0.0;w5=0.0;w6=0.0 #--bone weight
						ob = bpy.data.objects.get("b_255_0")
						
						
						ms = bpy.data.objects.get("MeshScale")
						if ms != None:
							print (" b_255_0, found ob.scale = ", ms.scale)
							MeshScale = 32768/(ms.scale[0])
						else:
							print (" cannot find b_255_0")
							MeshScale = 32768/228.0
						#MeshScale = 32768.0
						
						Vert = [None] * vc
						for c in range(vc):
							V = mathutils.Vector(me.matrix_world*OutMesh.vertices[c].co)
							Vert[c] = mathutils.Vector([V.x, V.y, V.z])
						GroupVertArray[i][k] = Vert
						
						#  Bi-Normal (Bi-Tangent) and Tangent
						tan1 = [None] * vc
						tan2 = [None] * vc
						Tangent = [None] * vc
						BiTangent = [None] * vc
						Tan_w = [ 0.0 ] * vc
						for c in range(vc):
							tan1[c] = mathutils.Vector([0.0,0.0,0.0])
							tan2[c] = mathutils.Vector([0.0,0.0,0.0])
						
						for c in range(fc):				
							fv = OutMesh.polygons[c].vertices							
							# calculate	 tangent and bi-tangent,  
							# Lengyel, Eric. “Computing Tangent Space Basis Vectors for an Arbitrary Mesh”. Terathon Software 3D Graphics Library, 2001. http://www.terathon.com/code/tangent.html
							i1 = fv[0]; i2= fv[1] ; i3 = fv[2]		
							
							v1 = Vert[i1]
							v2 = Vert[i2]
							v3 = Vert[i3]
							#v1.y = -v1.y;	v2.y = -v2.y;	v3.y = -v3.y; # mk9 use flipped y direction
							x1 = v2.x - v1.x
							x2 = v3.x - v1.x
							y1 = v2.y - v1.y
							y2 = v3.y - v1.y
							z1 = v2.z - v1.z					
							z2 = v3.z - v1.z
							w1 = MeshUV[i1]
							#w1.y = 1.0-w1.y
							w2 = MeshUV[i2]
							#w2.y = 1.0-w2.y
							w3 = MeshUV[i3]							
							#w3.y = 1.0-w3.y
							
							s1 = w2.x - w1.x
							s2 = w3.x - w1.x
							t1 = w2.y - w1.y
							t2 = w3.y - w1.y
							divr = (s1* t2 - s2 * t1)
							if divr ==0.0:
								divr = 0.001
							r = 1.0 / divr
							sdir = mathutils.Vector([(t2*x1 - t1 *x2)*r, (t2* y1- t1*y2)*r, (t2 * z1 - t1 *z2) *r])
							tdir = mathutils.Vector([(s1*x2 - s2 *x1)*r, (s1* y2- s2*y1)*r, (s1 * z2 - s2 *z1) *r])
							tan1[i1] += sdir; tan1[i2] += sdir; tan1[i3]+= sdir
							tan2[i1] += tdir; tan2[i2] += tdir; tan2[i3]+= tdir
						# calculate	 tangent and bitangent(aka binormal)	
						for c in range(vc):
							n = NormArray[c]
							t = tan1[c]
							Tangent[c] = ( t - n * n.dot(t)).normalized()
							
							if (n.cross(t)).dot( tan2[c]) < 0.0:
								Tan_w[c] = -1.0
							else:
								Tan_w[c]  = 1.0
							BiTangent[c] = n.cross( Tangent[c]) * Tan_w[c]
							#print ("tan1= ", tan1[c],"tan2= ",tan2[c],"tangent= ",Tangent[c],"bi-tan= ",BiTangent[c])
						GroupTanArray[i][k] = Tangent
						GroupBiNrmArray[i][k] = BiTangent
						
						
						def makeUniqueArray(seq): # Dave Kirby
							# Order preserving
							seen = set()
							return [x for x in seq if x not in seen and not seen.add(x)]							
						#Build fast vertex group index -> bone_id lookup table
						for vg in me.vertex_groups:
							VGroupLUT[i][vg.index]=int(re.split('_',vg.name)[2]) 

						bone_set = set()
						max_bone = 0	 # find out the total number of active bones
						#VertWeight = []					 
						for c in range( vc):					 
							bc = len (OutMesh.vertices[c].groups)  
							active_bone = 0
							for j in range(bc):
								if OutMesh.vertices[c].groups[j].weight > 0:
									#bid = GetVertexBoneID(me, OutMesh.vertices[c], j)									
									bid = GetVertexBoneID(VGroupLUT[i], OutMesh.vertices[c], j)	
									bone_set.add(bid)
									#VertWeight.append([bid,OutMesh.vertices[c].groups[j].weight])
									active_bone += 1
							if active_bone > max_bone:
								max_bone = active_bone							
						if max_bone > 4:
							max_bone = 4
						# extend bonemap if new mesh use more bones	
						new_bone_map = sorted(list( bone_set))
						print(" new bone list ",i,len(new_bone_map),new_bone_map)
						for b in new_bone_map:
							try:
								ind = boneMap.index(b)
							except ValueError:							  
								boneMap.append(b)		
						print("mesh ",i," modify vc new_end" ,vc,total_vc, new_end)												   
						print ("mesh ",i,k,len(boneMap),boneMap)						
						
						real_vc = vc					
						
						vdiff = max_vend -vstart
						if vend > max_vend:
							max_vend = vend						
						NewGroupArray[i][k]	   = [vc,fc,total_vc,vend-vstart,vdiff, vc]
																	
						reset = True
					else:  # mesh is not mark (selected) as modified
						# Aman: TR9 face groups within a mesh share same vertex buffer, I don't known yet how to create face groups inside a mesh object in Blender
						# if any group inside a mesh is marked for export, all groups  in same mesh will get there copy of vertices info during export. 
						last_max_vend = max_vend  
						vc = vend-vstart
						vdiff = max_vend -vstart
						if vend > max_vend:
							max_vend = vend												
						if debug:
							print("mesh ",i, "vc ",vc, "vstart vend",vstart ,vend)
						
						NewGroupArray[i][k]	   = [vc,fc,total_vc,vend,vdiff,total_vc]
						
										 
					meshGroupIdx += 1					 
					total_vc += vc

				# new mesh expand vertex buffer end. include them	
				#if new_end > total_vc:
				#	total_vc = new_end
				MeshInfoArray[i][9] =  total_vc						 
				#WriteShort (nf, fc)					
				NewMeshInfo[i] = [True,total_vc,fc,sc,None,None]				
				Bone_array[i]=boneMap #sorted(list(boneMap)), do not sort, sorting mess up untouched meshes
				if (len(boneMap) > 42):
					print(" Mesh %d bone map exceed 42 bones !!!!" % i)
					#self.report({'ERROR'}, "Mesh %d bound to too many bones! Divided it into smaller meshes." %i)
					bpy.ops.error.message('INVOKE_DEFAULT', 
						type = "Error",
						message = 'Mesh %d bound to more than 42 bones. Please divide it into smaller meshes' % i)
					f.close()
					nf.close()	
					return 
				
				if debug:
					print ("total vc", total_vc)
				#boneMapOffsetDiff += (len (bone_map) - meshInfo[2]	 )				  
			else:				 
				#WriteShort(nf, fc)
				meshGroupIdx += meshInfo[0]
				NewMeshInfo[i] = [False,0,0,0,None,None]
				print("mesh ",i," orig vc " ,meshInfo[9])
			if meshInfo[3] == 0: # NoBoneMap
				# vertex buffer come right after mesh info array
				bmOffsetStart = uiOffsetMeshInfo + alignedMeshInfo	
			else:
				if i == 0:
					bmOffsetStart = uiOffsetMeshInfo + alignedMeshInfo	
					print("bmOffsetStart ",hex(meshInfo[3]),hex(extraMeshInfo), hex(bmOffsetStart))
					MeshInfoArray[i][3]=bmOffsetStart
					bmOffsetDiff = 0
				else:										 
					MeshInfoArray[i][3] = bmOffsetStart
			new_bmSize = len(boneMap)
			#print(" new bmSize ",new_bmSize," orig ",meshInfo[2],"bmOffsetStart ",hex(bmOffsetStart))
			#print(" bm start orig",hex( meshInfo[3]),"bmOffsetStart ",hex(bmOffsetStart),"extra mesh ",hex(extraMeshInfo),hex(meshInfo[3]))
			MeshInfoArray[i][2] = new_bmSize											
			bmOffsetStart += (len(boneMap)*4)
			#  32 bytes	 aligned
			bmOffsetStart = (bmOffsetStart +31)&0xffffffe0
			#MeshInfoArray[i]=list(meshInfo) # saved in array
			BoneMapArray[i]=boneMap								
			
		VertBlockStart = bmOffsetStart
		print(" before meshinfo ", hex(VertBlockStart))
		meshInfoStart = uiOffsetMeshInfo
		for i in range(usNumMeshTot):  # write mesh info array
			meshInfo = SaveInfoArray[i]
			f.seek(offsetStart + offsetMeshStart + meshInfo[8] + 0x8, SEEK_SET)
			usNumVertexComponents = ReadShort(f)
			ucMeshVertStride = ReadByte(f)		  
			VCompSize = MeshInfoArray[i][4] - MeshInfoArray[i][8] 
			MeshInfoArray[i][8] = VertBlockStart
			VertBlockStart += VCompSize
			MeshInfoArray[i][4] = VertBlockStart			
			if NewMeshInfo[i][0] == True and debug: # modified
				print (" Modified ")				
			VBuffSize = MeshInfoArray[i][9]*ucMeshVertStride

			VBuffSize = (VBuffSize +31)&0xffffffe0	#  32 bytes	 aligned
			#print (" vbuf ", hex(VBuffSize), MeshInfoArray[i][9] , hex(ucMeshVertStride))			 
			NewMeshInfo[i][4] = VBuffSize
			VertBlockStart += VBuffSize			   

			print ( "mesh info 8 4 ",hex(meshInfo[8]),hex(MeshInfoArray[i][8]),hex(meshInfo[4]),hex(MeshInfoArray[i][4]))
			# Write MeshInfo
			#MeshInfo = unpack('1i2h10i',f.read(48))
			if debug:
				print (" new meshinfo start ", hex(nf.tell()-(offsetStart + offsetMeshStart)), "offset ",hex(meshInfoStart),)
			WriteLong(nf,MeshInfoArray[i][0])
			WriteShort(nf,MeshInfoArray[i][1])
			WriteShort(nf,MeshInfoArray[i][2])
			WriteLong(nf,MeshInfoArray[i][3])
			WriteLong(nf,MeshInfoArray[i][4])
			WriteLong(nf,MeshInfoArray[i][5])
			WriteLong(nf,MeshInfoArray[i][6])
			WriteLong(nf,MeshInfoArray[i][7])
			WriteLong(nf,MeshInfoArray[i][8])
			WriteLong(nf,MeshInfoArray[i][9])
			WriteLong(nf,MeshInfoArray[i][10])
			WriteLong(nf,MeshInfoArray[i][11])
			WriteLong(nf,MeshInfoArray[i][12])				

			meshInfoStart +=0x30
			
		NextStart = (meshInfoStart +31)&0xffffffe0	#  32 bytes	 aligned	  
		for j in range(NextStart - meshInfoStart):
			WriteByte(nf,0)	  
		if debug:
			print (" bonemap next start ", hex(NextStart))
		
		#write bone map
		
		newBoneTableStart = NextStart
		CurrOffset = NextStart	# bone table start
		for i in range(usNumMeshTot):	 
			meshInfo = SaveInfoArray[i]		   
			if debug:
				print (" new bonemap start ", hex(nf.tell()-(offsetStart + offsetMeshStart))," orig start ,new start", hex(meshInfo[3]),hex(MeshInfoArray[i][3]))
			#print("check bone start ",hex(CurrOffset), " meshInfo ",hex(MeshInfoArray[i][3]))
			for j in range(MeshInfoArray[i][2]):
				WriteLong(nf, BoneMapArray[i][j])			 
			CurrOffset += (4 * MeshInfoArray[i][2])				  
			NextStart = (CurrOffset +31) & 0xffffffe0 
			for j in range((NextStart-CurrOffset)):
				WriteByte(nf,0)
			CurrOffset = NextStart

		#write Vertex block
		for i in range(usNumMeshTot):  
			meshInfo = SaveInfoArray[i]
			if debug:
				print("Vcomp start ",hex(nf.tell()-(offsetStart + offsetMeshStart)), " NewInfo ",hex(MeshInfoArray[i][8])," orig ",hex(meshInfo[8]))
			VCompSize = meshInfo[4] - meshInfo[8] 
			f.seek(offsetStart + offsetMeshStart + meshInfo[8], SEEK_SET)				 

			if NewMeshInfo[i][0] == False:	
				# write vertex component
				for j in range(int(VCompSize/4)):
					temp = ReadLong(f)
					WriteLong(nf,temp)			  
				# write vert buffer					  
				# if no modification, a straight copy
				print("VBuff start ",hex(nf.tell()-(offsetStart + offsetMeshStart)), " NewInfo ",hex(MeshInfoArray[i][4])," orig ",hex(meshInfo[4]),"vc ",MeshInfoArray[i][9]," ",meshInfo[9])	  
				
				VertSize = int(NewMeshInfo[i][4]/4)
				for j in range(VertSize):
					temp = ReadLong(f)
					WriteLong(nf,temp)					


				NextStart = MeshInfoArray[i][4]
				NextStart += NewMeshInfo[i][4]
			else:
				print("Modified ")
				f.seek(offsetStart + offsetMeshStart + meshInfo[8], SEEK_SET)								 
				startpos = nf.tell()
				tempbuf = f.read(8)
				nf.write(tempbuf)
				
				usNumVertexComponents = ReadShort(f)
				WriteShort(nf,usNumVertexComponents)
				ucMeshVertStride = ReadByte(f)
				WriteByte(nf,ucMeshVertStride)
				#f.seek(0x5, SEEK_CUR)
				tempbuf = f.read(5)
				nf.write(tempbuf)

				iMeshVertPos = -1
				iMeshNrmPos = -1
				iMeshTessNrmPos = -1
				iMeshTangPos = -1
				iMeshBiNrmPos = -1
				iMeshPckNTBPos = -1
				iMeshBwPos = -1
				iMeshBiPos = -1
				iMeshCol1Pos = -1
				iMeshCol2Pos = -1
				iMeshUV1Pos = -1
				iMeshUV2Pos = -1
				iMeshUV3Pos = -1
				iMeshUV4Pos = -1
				iMeshIIDPos = -1
				# Mod tool only supports, position, norm, bi-normal,tangent, uv1,uv2,col1)							
				# need to disable some vertex components. this will remove some features/effects from mesh.
				comp_start = f.tell()
				for j in range(usNumVertexComponents): # search and find Vertex position offset value
					uiEntryHash = ReadLong(f)
					usEntryValue = ReadShort(f)
					ucEntryType = ReadByte(f)
					ucEntryNull = ReadByte(f)
					# a hack to disable some of the components not support by mod tool
					# will override unsupported feature with VertexPos id and offset.
					if uiEntryHash == 0xD2F7D823:#Position
						iMeshVertPos = usEntryValue
						VertPosType = ucEntryType
						print("Found VertexPos " + "Pos: " + str(usEntryValue))
				f.seek(comp_start, SEEK_SET)	  
				for j in range(usNumVertexComponents):
					uiEntryHash = ReadLong(f)
					usEntryValue = ReadShort(f)
					ucEntryType = ReadByte(f)
					ucEntryNull = ReadByte(f)
					print ("UsHash "+hex(uiEntryHash), "usEntryValue "+hex(usEntryValue))
					if uiEntryHash == 0xD2F7D823:#Position
						iMeshVertPos = usEntryValue
						print("VertexPos " + "Pos: " + str(usEntryValue))
					elif uiEntryHash == 0x36F5E414:#Normal
						iMeshNrmPos = usEntryValue
						#uiEntryHash = 0xD2F7D823
						#usEntryValue = iMeshVertPos							
					elif uiEntryHash == 0x3E7F6149:#TessellationNormal
						if debug:
							print("Unsupported Vertex Component: TessellationNormal! " + "Pos: " + str(usEntryValue))
						# a hack to disable some of the components not support by mod tool							
						#	iMeshTessNrmPos = usEntryValue
						uiEntryHash = 0xD2F7D823
						usEntryValue = iMeshVertPos	
						ucEntryType = VertPosType
					elif uiEntryHash == 0xF1ED11C3:#Tangent
						#if debug:
						#	print("Unsupported Vertex Component: BiNormal! " + "Pos: " + str(usEntryValue))
						#uiEntryHash = 0xD2F7D823
						#usEntryValue = iMeshVertPos							
						iMeshTangPos = usEntryValue						  
					elif uiEntryHash == 0x64A86F01:#Binormal
						#if debug:
						#	print("Unsupported Vertex Component: BiNormal! " + "Pos: " + str(usEntryValue))
						#uiEntryHash = 0xD2F7D823
						#usEntryValue = iMeshVertPos							
						iMeshBiNrmPos = usEntryValue
					elif uiEntryHash == 0x9B1D4EA:#PackedNTB
						if debug:
							print("Unsupported Vertex Component: PackedNTB! " + "Pos: " + str(usEntryValue))
						uiEntryHash = 0xD2F7D823
						usEntryValue = iMeshVertPos							   
						ucEntryType = VertPosType
					#	iMeshPckNTBPos = usEntryValue
					elif uiEntryHash == 0x48E691C0:#SkinWeights
						iMeshBwPos = usEntryValue
					elif uiEntryHash == 0x5156D8D3:#SkinIndices
						iMeshBiPos = usEntryValue
					elif uiEntryHash == 0x7E7DD623:#Color1
						if debug:
							print("Unsupported Vertex Component: Color1! " + "Pos: " + str(usEntryValue))
						uiEntryHash = 0xD2F7D823
						usEntryValue = iMeshVertPos		  
						ucEntryType = VertPosType
					#	 iMeshCol1Pos = usEntryValue						
					elif uiEntryHash == 0x733EF0FA:#Color2
						if debug:
							print("Unsupported Vertex Component: Color2! " + "Pos: " + str(usEntryValue))
						uiEntryHash = 0xD2F7D823
						usEntryValue = iMeshVertPos	
						ucEntryType = VertPosType	
					#	iMeshCol2Pos = usEntryValue
					elif uiEntryHash == 0x8317902A:#Texcoord1
						iMeshUV1Pos = usEntryValue
					elif uiEntryHash == 0x8E54B6F3:#Texcoord2
						iMeshUV2Pos = usEntryValue
					elif uiEntryHash == 0x8A95AB44:#Texcoord3
						if debug:
							print("Unsupported Vertex Component: Texcoord3! " + "Pos: " + str(usEntryValue))
						uiEntryHash = 0xD2F7D823
						usEntryValue = iMeshVertPos							   
						ucEntryType = VertPosType
					#	iMeshUV3Pos = usEntryValue
					elif uiEntryHash == 0x94D2FB41:#Texcoord4
						if debug:
							print("Unsupported Vertex Component: Texcoord4! " + "Pos: " + str(usEntryValue))
						uiEntryHash = 0xD2F7D823
						usEntryValue = iMeshVertPos							   
						ucEntryType = VertPosType
					#	iMeshUV4Pos = usEntryValue
					elif uiEntryHash == 0xE7623ECF:#InstanceID
						if debug:
							print("Unsupported Vertex Component: InstanceID! " + "Pos: " + str(usEntryValue))
						uiEntryHash = 0xD2F7D823
						usEntryValue = iMeshVertPos			
						ucEntryType = VertPosType
					#	iMeshIIDPos						   
					else:
						if debug:
							print("Unknown Vertex Component! Hash: " + str(hex((uiEntryHash))) + " value: " + str(usEntryValue))
					WriteLong(nf,uiEntryHash) 
					WriteShort(nf,usEntryValue) 
					WriteByte(nf,ucEntryType) 
					WriteByte(nf,ucEntryNull)
				tempsize = nf.tell()-startpos
				for j in range(VCompSize-tempsize):	 # make sure it is 32 bytes aligned
					WriteByte(nf,0)
				print("VBuff start ",hex(nf.tell()-(offsetStart + offsetMeshStart)), " NewInfo ",hex(MeshInfoArray[i][4])," orig ",hex(meshInfo[4]),"vc ",MeshInfoArray[i][9]," ",meshInfo[9])	  
				vbuff_start = nf.tell()
				
				print("curr offset ",hex(nf.tell()-(offsetStart + offsetMeshStart)))
				end_of_vbuff = nf.tell()
				print ("MeshChange",i, MeshChange[i])
				max_vend = 0
				
				newVertBuff = bytearray(b'\x00' * (MeshInfoArray[i][9] * ucMeshVertStride))
				
				startv = 0
				for j in range(MeshInfoArray[i][0]):
					
					if j in MeshChange[i]:	#  this group need to be replaced
						sc = MeshChange[i][j]
						try:
							if i < usNumMesh:
								obj = SelectMeshInfo[sc][0]
							else:
								obj = addMeshInfo[i-usNumMesh][0]
							OutMesh = obj.to_mesh(context.scene, True, 'PREVIEW', calc_tessface=False)
						except RuntimeError:
							OutMesh = None

						if OutMesh is None:
							continue  
						vc = len(OutMesh.vertices)										

						vc = NewGroupArray[i][j][5]						   
						#construct vertex buffer for new group (sub-mesh)						
						#newVertBuff = bytearray(b'\x00' * (vc * ucMeshVertStride))
						print ("mesh i j vc, vsize, start", i, j, vc, vc * ucMeshVertStride, NewGroupArray[i][j][2])
						
						'''						
						if NewGroupArray[i][j][3] <= max_vend:
							idx = NewGroupArray[i][j][2]*ucMeshVertStride							 
						else:
							idx = startv #idx = 0
						'''				
						idx = idx = NewGroupArray[i][j][2]*ucMeshVertStride							   
						
						if debug:
							print ("mesh ",i,Bone_array[i])		
						if i < usNumMesh:
							me = SelectMeshInfo[sc][0]
						else:
							me = addMeshInfo[i-usNumMesh][0]						
						for c in range(vc):
							
							bc = len (OutMesh.vertices[c].groups)
							w_array = [] #[None] * bc
							for bi in range( bc ):						  
								#bb = GetVertexBoneID(me, OutMesh.vertices[c], bi) 
								bb = GetVertexBoneID(VGroupLUT[i], OutMesh.vertices[c], bi)	
								ww = OutMesh.vertices[c].groups[bi].weight
								if bb in Bone_array[i]:
									w_array.append( [ww,bb])
								#print( "b ", bb ," w ",ww)
								#--format "% (%,%)" j bb ww																							
							#-- sort bone by weight, only use top 4 bones.								
							w_array.sort( key=itemgetter(0), reverse=True)
							
							w1=w2=w3=w4=0.0
							bi1=bi2=bi3=bi4=0
							
							#print ("i,j bc",i,j,bc)
							#print (w_array[0][1])
							bc = len(w_array)
							if (bc > 0 and w_array[0][0] >0 ):
								#print("bc c bi1",bc,c,w_array[0][1],w_array[0][0])
								bi1 = Bone_array[i].index(w_array[0][1]); 
								#if bi1 >=meshInfo[2]+2:
								#	bi1 = 0
								w1= w_array[0][0]
							if (bc > 1 and w_array[1][0] >0 ):
								#print("bi2",w_array[1][1],w_array[1][0])
								bi2 = Bone_array[i].index(w_array[1][1]); 
								#if bi2 >=meshInfo[2]+2:
								#	bi2 = 0								   
								w2= w_array[1][0]
							if (bc > 2 and w_array[2][0] >0 ):
								#print("bi3",w_array[2][1],w_array[2][0])
								bi3 = Bone_array[i].index(w_array[2][1]); 
								#if bi3 >=meshInfo[2]+2:
								#	bi3 = 0								   
								w3= w_array[2][0]
							if (bc > 3 and w_array[3][0] >0 ):
								#print("bi4",w_array[3][1],w_array[3][0])
								bi4 = Bone_array[i].index(w_array[3][1]); 
								#if bi4 >=meshInfo[2]+2:
								#	bi4 = 0																   
								w4= w_array[3][0]	  
								   
							#-- make sure all weight sum up to 255 exactly		
							wt = w1+w2+w3+w4
							if wt == 0.0:
								w1 = w2 = w3 =w4 = 0
							else: 
								if wt > 1.0:
									wt = 1.0
								wt = 255.0/wt
								w1 = int(w1*wt)
								w2 = int(w2*wt)
								w3 = int(w3*wt)
								w4 = int(w4*wt)								
								adj = 255 - (w1+w2+w3+w4)
								w1 += adj  
												
							if iMeshVertPos != -1:
								pos = idx + iMeshVertPos
								newVertBuff[pos:pos+0xc]=pack("fff",GroupVertArray[i][j][c].x,GroupVertArray[i][j][c].y,GroupVertArray[i][j][c].z)
							if iMeshNrmPos != -1:
								pos=idx + iMeshNrmPos							
								newVertBuff[pos:pos+3]=pack("BBB",int(GroupNormArray[i][j][c].x*127+127),int(GroupNormArray[i][j][c].y*127+127),int(GroupNormArray[i][j][c].z*127+127))
							if iMeshTangPos != -1:
								pos=idx + iMeshTangPos							 
								newVertBuff[pos:pos+3]=pack("BBB",int(GroupTanArray[i][j][c].x*127+127),int(GroupTanArray[i][j][c].y*127+127),int(GroupTanArray[i][j][c].z*127+127))
							if iMeshBiNrmPos != -1:
								pos=idx + iMeshBiNrmPos							  
								newVertBuff[pos:pos+3]=pack("BBB",int(GroupBiNrmArray[i][j][c].x*127+127),int(GroupBiNrmArray[i][j][c].y*127+127),int(GroupBiNrmArray[i][j][c].z*127+127))
							if iMeshUV1Pos	!= -1:
								pos = idx + iMeshUV1Pos 
								#print ("UV",GroupUVArray[i][j][c].x,GroupUVArray[i][j][c].y)
								newVertBuff[pos:pos+4]=pack("hh",int(GroupUVArray[i][j][c].x*2048),int((GroupUVArray[i][j][c].y)*2048))
							if iMeshUV2Pos	!= -1:
								pos = idx + iMeshUV2Pos 
								newVertBuff[pos:pos+4]=pack("hh",int(GroupUVArray[i][j][c].x*2048),int((GroupUVArray[i][j][c].y)*2048)) 
							if iMeshBiPos  != -1:							
								pos = idx + iMeshBiPos 
								newVertBuff[pos:pos+4]=pack("4B",bi1,bi2,bi3,bi4)										
							if iMeshBwPos  != -1:							
								pos = idx + iMeshBwPos 
								newVertBuff[pos:pos+4]=pack("4B",w1,w2,w3,w4)											
							idx += ucMeshVertStride
						
						
					else:
						vc = NewGroupArray[i][j][0]			 
						print("copy vc ",vc, "new group	 array vertex start",NewGroupArray[i][j][2])
						idx = NewGroupArray[i][j][2]*ucMeshVertStride	#startv
						#construct vertex buffer for new group (sub-mesh)
						print ("copy old mesh vc",vc)
						if vc > 0:
							#newVertBuff = bytearray(b'\x00' * (vc * ucMeshVertStride))					   
							vend = NewGroupArray[i][j][3] 
							start_offset = vend - vc
							#print ("start_offset ", start_offset)
							f.seek(offsetStart + offsetMeshStart + meshInfo[4] + (start_offset *ucMeshVertStride), SEEK_SET)							
							
							inBuf = f.read(vc * ucMeshVertStride)
							tempVertBuff=bytearray(inBuf)
							#print ("inbuf ", inBuf)
												
							idx1 = 0
							#if iMeshBiPos	!= -1:	  
				
							for c in range(vc):
								bi1=bi2=bi3=bi4=0
								pos = idx #+ iMeshBiPos 
								pos1 = idx1 #+ iMeshBiPos 
								newVertBuff[idx:idx+ucMeshVertStride]=tempVertBuff[idx1:idx1+ucMeshVertStride]						 
								idx += ucMeshVertStride
								idx1 += ucMeshVertStride
							
							
					if NewGroupArray[i][j][3] > max_vend:
						max_vend = NewGroupArray[i][j][3]
					startv+= NewGroupArray[i][j][0]*ucMeshVertStride   # advance vertex start pointer , account for overlap
				nf.write(newVertBuff)					 
				if debug:
					print (" newVertBuff size ",len(newVertBuff))
				#nf.seek(end_of_vbuff, SEEK_SET)		   
				CurrOffset =  MeshInfoArray[i][4]						
				print("curr offset ",hex(nf.tell()-(offsetStart + offsetMeshStart)), hex(CurrOffset), MeshInfoArray[i][9], hex(ucMeshVertStride), meshInfo[9])	
					
				CurrOffset += MeshInfoArray[i][9]*ucMeshVertStride	 
				print ("curr", hex(CurrOffset))
				NextStart = (CurrOffset +31) & 0xffffffe0 
				print (" next  ", hex(NextStart))				 
				
				for j in range((NextStart-CurrOffset)):
					print ( "write byte")
					WriteByte(nf,0)				   
		OffsetDiff = NextStart - uiOffsetFaceData					
		
		print("face start ",hex(nf.tell()-(offsetStart + offsetMeshStart)), " New offset ",hex(NextStart)," orig ",hex(uiOffsetFaceData))	
		
		NewFaceOffset = NextStart				
		#write face index block
		meshGroupIdx = 0
		VStart	= 0 
		MeshGroupMap = [dict() for x in range(usNumMeshTot)]	
		
		for i in range(usNumMeshTot):  
			meshInfo = SaveInfoArray[i]
			NewStart = meshInfo[9] # end of old vbuff
			CurrVIdx = 0
			VDiff = 0
			last_vend = 0
			max_vend = 0
			#VIdx = meshInfo[9]	 # staring idx for new mesh
			VIdx = 0
			for j in range(MeshInfoArray[i][0]):
				if (i< usNumMesh):
					MeshGroupMap[i][j]=meshGroupIdx;
				else:
					srcMeshId=int(addMeshInfo[i-usNumMesh][1])
					srcSubId = int(addMeshInfo[i-usNumMesh][2])
					meshGroupIdx = MeshGroupMap[srcMeshId][srcSubId]				
				f.seek(offsetStart + offsetMeshStart + uiOffsetMeshGroupInfo + meshGroupIdx * 0x50, SEEK_SET)
				meshGroupIdx += 1
				meshGroupInfo = unpack("iiiiiiiiiiiiiiiiiiii",f.read(80))			
				
				if NewMeshInfo[i][0] == True and (j in MeshChange[i]):
					vc = NewGroupArray[i][j][5]
					
					fc = NewGroupArray[i][j][1]
					si = MeshChange[i][j]
					if i < usNumMesh:
						OutMesh = SelectMeshInfo[si][0] #--对应选择的 Mesh
					else:
						OutMesh = addMeshInfo[i-usNumMesh][0]
					fvc = int(fc/3)					
					#--print fvc
					if debug:
						print ( "fvc = " ,fvc , " poly len = " , len (OutMesh.data.polygons))
						print("mesh i,j",i,j," face start ",hex(VStart)," orig ",hex(meshGroupInfo[4]))	   
					
					for c in range(fc):
						fv = OutMesh.data.polygons[c].vertices
						WriteShort (nf, fv[0]+VIdx)
						WriteShort (nf, fv[1]+VIdx)
						WriteShort (nf, fv[2]+VIdx) 
						
					VDiff += NewGroupArray[i][j][4]	
					VDiff +=(vc -  NewGroupArray[i][j][3])
					VIdx += vc	
					
				else:		 
					if debug:
						print("mesh i,j",i,j," face start ",hex(VStart)," orig ",hex(meshGroupInfo[4]))				   
					#rapi.rpgSetName("Mesh_" + str(meshIndex) + "_" + str(i))
					#rapi.rpgSetPosScaleBias((fDefaultMeshScale, fDefaultMeshScale, fDefaultMeshScale), (0, 0, 0))					
					f.seek(offsetStart + offsetMeshStart + uiOffsetFaceData + meshGroupInfo[4] * 0x2, SEEK_SET)
					
					fc = meshGroupInfo[5]
					
			
					print ("fc ",fc)
					if	NewMeshInfo[i][0] == True:
						vc = NewGroupArray[i][j][0]
						VIdx+=vc
						VDiff += NewGroupArray[i][j][4]
						for c in range(fc):			   
							i1 = ReadShort(f)
							i2 = ReadShort(f)
							i3 = ReadShort(f)
							vstart = NewGroupArray[i][j][2]							   
							WriteShort (nf, i1+VDiff)
							WriteShort (nf, i2+VDiff)
							WriteShort (nf, i3+VDiff)
							vend = NewGroupArray[i][j][3]
							last_vend = vend

					else:	
						for c in range(fc):			   
							i1 = ReadShort(f)
							i2 = ReadShort(f)
							i3 = ReadShort(f)
							WriteShort (nf, i1)
							WriteShort (nf, i2)
							WriteShort (nf, i3)										   
				 
				VStart += (fc*3)
				
				if NewMeshInfo[i][0] == True:
					CurrVIdx += NewGroupArray[i][j][0]
					if NewGroupArray[i][j][3] > max_vend:
						max_vend = NewGroupArray[i][j][3]
					
				
		NextStart += (VStart*2)
		NewIndexCount = VStart # new total Index count		
		
		CurrOffset	= NextStart
		NextStart = (CurrOffset +31) & 0xffffffe0
		for i in range(NextStart-CurrOffset):
			WriteByte(nf, 0)			
		OffsetDiff = NextStart - uiOffsetMeshGroupInfo 
		
		print("Group start ",hex(nf.tell()-(offsetStart + offsetMeshStart)), " New offset ",hex(NextStart)," orig ",hex(uiOffsetMeshGroupInfo))	  
		print("Group start ",hex(nf.tell()), " New offset ",hex(NextStart+(offsetStart + offsetMeshStart))," orig ",hex(uiOffsetMeshGroupInfo))	  
		
		NewOffsetMeshGroupInfo = NextStart	  
		# write GroupInfo
		faceOffset = 0
		meshGroupIdx = 0
		total_face = 0
		

		for i in range(usNumMeshTot):
			lastFaceOffset = faceOffset
			for j in range(MeshInfoArray[i][0]):
				if (i >= usNumMesh):  # we have a new mesh group here, copy group info from	 existing group
					srcMeshId=int(addMeshInfo[i-usNumMesh][1])
					srcSubId = int(addMeshInfo[i-usNumMesh][2])
					meshGroupIdx = MeshGroupMap[srcMeshId][srcSubId]
				f.seek(offsetStart + offsetMeshStart + uiOffsetMeshGroupInfo + meshGroupIdx * 0x50, SEEK_SET)

				meshGroupIdx += 1

				meshGroupInfo = unpack("iiiiiiiiiiiiiiiiiiii",f.read(80))	 
				ngi = list(meshGroupInfo)
				if NewMeshInfo[i][0] == True and (j in MeshChange[i]):
					
					fc = NewGroupArray[i][j][1]
					print ("mesh i j", i,j, "changed fc",fc)
					ngi[5] = fc					  
					ngi[6] = NewGroupArray[i][j][5]	 # vertex count
				else:
					fc = meshGroupInfo[5]
				ngi[4] = faceOffset
				
				print (" new face offset ", ngi[4], " orig ",meshGroupInfo[4]," fc ",fc)
				nf.write(pack("iiiiiiiiiiiiiiiiiiii",ngi[0],ngi[1],ngi[2],ngi[3],ngi[4],ngi[5],ngi[6],ngi[7],ngi[8],
					ngi[9],ngi[10],ngi[11],ngi[12],ngi[13],ngi[14],ngi[15],ngi[16],ngi[17],ngi[18],ngi[19]))
				#for k in range(20):
				#	 WriteLong(nf,newGroupInfo[k])
				faceOffset += (fc * 3)
				total_face += fc
			lastpos = nf.tell()	
			nf.seek(offsetStart + offsetMeshStart + uiOffsetMeshInfo + i * 0x30+ 40 , SEEK_SET)
			WriteLong(nf,lastFaceOffset)				  #update meshInfo indexStartOffset 
			WriteLong(nf,total_face)				  #update meshInfo index_count 
			lastfo=lastFaceOffset
			lasttf=total_face
			total_face = 0
			nf.seek(lastpos, SEEK_SET)
			
		NewFileSize = nf.tell()			
		nf.seek(OffsetMeshFileSize, SEEK_SET)		 
		WriteLong(nf,(NewFileSize-offsetMeshStart-offsetStart))	 # write new file size
		WriteLong(nf, NewIndexCount) # update total index count
		nf.seek(GroupInfoHeaderOffset, SEEK_SET)
		WriteLong(nf,NewOffsetMeshGroupInfo)
		nf.seek(FaceDataHeaderOffset, SEEK_SET)

		WriteLong(nf,NewFaceOffset)
		
		nf.seek(BoneMapHeaderOffset, SEEK_SET)
		if bHasBoneMap == True:
			WriteLong(nf, (uiOffsetBoneMap+extraMeshInfo))
			WriteLong(nf, (uiOffsetBoneMap2+extraMeshInfo))
		nf.seek(numGroupHeader,SEEK_SET)
		WriteShort(nf,usNumMeshGroups + usNumAddMesh)
		WriteShort(nf,usNumMeshTot )
		
		
		print("MeshGroupOffset old, new ",hex(uiOffsetMeshGroupInfo),hex(NewOffsetMeshGroupInfo))
		print("FaceOffset orig, new ", hex(uiOffsetFaceData), hex(NewFaceOffset))

		print("MeshGroupOffset old, new ",hex(uiOffsetMeshGroupInfo+(offsetStart + offsetMeshStart)),hex(NewOffsetMeshGroupInfo+(offsetStart + offsetMeshStart)))
		print("FaceOffset orig, new ", hex(uiOffsetFaceData+(offsetStart + offsetMeshStart)), hex(NewFaceOffset+(offsetStart + offsetMeshStart)))

		
		f.close ()
		nf.close ()
		self.report({'INFO'}, "Complete !")
		
	else: 
		if selcnt == 0:
			self.report({'ERROR'}, "ACTION ABORTED\n\nSelect a mesh first!")			
			#bpy.ops.error.message('INVOKE_DEFAULT', 
			#	type = "Error",
			#	message = 'Must select at least one mesh for export!')
			return 


def getInputFilenameMod(self, filename):
	checktype = filename.split('\\')[-1].split('.')[1]
	print ("------------",filename)
	if checktype.lower() != 'mesh':
		print ("  Selected file = ", filename)
		raise (IOError, "The selected input file is not a *.mesh file")
		#self.report({'INFO'}, ("Selected file:"+ filename))
	else:
		modimport(filename)

class IMPORT_OT_Mod(bpy.types.Operator):
	'''Load a TR9 mesh File'''
	bl_idname = "import_mesh_tr9.mod"
	bl_label = "Import TR9 mesh"
	bl_space_type = "PROPERTIES"
	bl_region_type = "WINDOW"
	bl_options = {'UNDO'}

	# List of operator properties, the attributes will be assigned
	# to the class instance from the operator settings before calling.
	filepath = StringProperty(
			subtype='FILE_PATH',
			)

	def execute(self, context):
		getInputFilenameMod(self, self.filepath)
		return {'FINISHED'}

	def invoke(self, context, event):
		wm = context.window_manager
		wm.fileselect_add(self)
		return {'RUNNING_MODAL'}
			
###### EXPORT OPERATOR #######
class Export_OT_Mod(bpy.types.Operator, ExportHelper):
	"""Export Selected Meshes to MOD file"""
	bl_idname = "export_mesh_tr9.mod"
	bl_label = "Export TR9 mesh"

	filename_ext = ".mesh"

	#@classmethod
	#def poll(cls, context):
	#	 return context.active_object.type in {'MESH', 'CURVE', 'SURFACE', 'FONT'}

	def execute(self, context):
		start_time = time.time()
		print('\n_____START_____')
		props = self.properties
		filepath = self.filepath
		filepath = bpy.path.ensure_ext(filepath, self.filename_ext)
		bSmoothOverlapVertex = context.scene.SmoothVertex
		exported = do_export(self, context, props, filepath, bSmoothOverlapVertex)

		if exported:
			print('finished export in %s seconds' %((time.time() - start_time)))
			print(filepath)

		return {'FINISHED'}

	def invoke(self, context, event):
		wm = context.window_manager

		if True:
			# File selector
			wm.fileselect_add(self) # will run self.execute()
			return {'RUNNING_MODAL'}
		elif True:
			# search the enum
			wm.invoke_search_popup(self)
			return {'RUNNING_MODAL'}
		elif False:
			# Redo popup
			return wm.invoke_props_popup(self, event)
		elif False:
			return self.execute(context)
			
class OBJECT_OT_ExcludeSelectVertex(bpy.types.Operator):
	bl_idname = "exclude.selected_vertices"
	bl_label = "Exclude Selected vertices"
 
	filename_ext = ".mesh"

	@classmethod
	def poll(cls, context):
		return context.active_object.mode in {'EDIT'}

	def execute(self, context):
		obj = context.edit_object
		if obj.type == 'MESH':
			mesh = obj.data
			for v in mesh.vertices:
				if v.select:
					v.bevel_weight = -10.0	# make up number
					print ("v=",v.bevel_weight)
					#v.ExcludeSmooth = BoolProperty(default=True)					 
		
		return {'FINISHED'}

bpy.types.Scene.MyInt = IntProperty(
	name = "Value", 
	description = "Property Value",
	default = 0,
	min = 0)

bpy.types.Scene.MyEnum = EnumProperty(
	items = [('lod','LOD','level of detail' ),
			 ('mat','MAT','material id'),
			 ('grp','Group','group id'),
			 ('dpy','Display','display type')],
	name = "Property", description = "Property Name", default = 'lod')

#
#	 Menu in UI region
#
class UIPanel(bpy.types.Panel):
	bl_label = "TR9 Mod Tool"
	bl_idname = "OBJECT_PT_import_export_MK9"
	bl_space_type = "VIEW_3D"
	bl_region_type = "TOOLS" 
	bpy.types.Scene.MyInt = IntProperty(
	name = "Bone id", 
	description = "Property Value",
	default = 1,
	min = 0)
	"""
	bpy.types.Scene.MyEnum = EnumProperty(
	items = [('lod','LOD','level of detail' ),
			 ('mat','MAT','material id'),
			 ('grp','Group','group id'),
			 ('dpy','Display','display type')],
	name = "Property", description = "Property Name", default = 'lod')
	"""
	bpy.types.Scene.SmoothVertex   = BoolProperty(default=False)
 
	def draw(self, context):
		layout = self.layout
		scn = context.scene
		layout.operator(IMPORT_OT_Mod.bl_idname)
		layout.operator(Export_OT_Mod.bl_idname)		
		layout.label("Assign single bone:")
		layout.prop(scn, 'MyInt', icon='BLENDER', toggle=True)
		#layout.prop(scn, 'MyEnum', expand = True)

		layout.operator("rename.selected_meshes")
		layout.prop(scn, 'SmoothVertex' , text ="Smooth Overlap Vertex")
		#layout.operator(OBJECT_OT_ExcludeSelectVertex.bl_idname)
 
#
#	 The button prints the values of the properties in the console.
#
 
class OBJECT_OT_RenameButton(bpy.types.Operator):
	bl_idname = "rename.selected_meshes"
	bl_label = "To selected meshes"
 
	def execute(self, context):
		selection = context.selected_objects		
		selcnt= len (selection)	   
		scn = context.scene
		prop='lod' #scn.MyEnum
		
		
		new_vgroup_name = None
		if prop == 'lod': 
			for bone in bpy.context.scene.objects['ArmObject'].data.bones:
				bone_id =  int(re.split('_',bone.name)[2])	#skinOps.GetVertexWeightBoneID theSkin c 1
				#print( "bone_id = ",bone_id)
				if bone_id == int(scn.MyInt):
					new_vgroup_name = bone.name
		
		for i in range(selcnt):
			sName = re.split('_',selection[i].name)
			print("sName = ", sName)
			if sName[0] == 'Mesh':				  
				mshHdr_matid = mshHdr_grp = mshHdr_mde = mshHdr_lod = 0
				if len(sName) >= 8:
					mshHdr_matid = int (re.split(':',sName[4])[1])
					mshHdr_grp = int (re.split( ':', sName[5])[1])
					mshHdr_mde = int (re.split( ':', sName[6])[1])
					mshHdr_lod = int (re.split( 'x', sName[3])[1])
	 
				if prop == 'lod':				 
					mshHdr_lod = int(scn.MyInt)
					try:
						obj = selection[i]
						me = obj.to_mesh(context.scene, True, 'PREVIEW', calc_tessface=False)
					except RuntimeError:
						me = None

					if me is None:
						continue  
					if new_vgroup_name != None:
						vc = len(me.vertices)						 
						selection[i].vertex_groups.clear()
						print("new_vgroup_name ",new_vgroup_name)
						vgroup = selection[i].vertex_groups.new(new_vgroup_name)
						for c in range (vc):
							vgroup.add([c],mshHdr_lod, 'ADD')

					
				elif prop == 'mat':
					mshHdr_matid = int(scn.MyInt)
				elif prop == 'grp':
					mshHdr_grp = int(scn.MyInt)
				elif prop == 'dpy':
					mshHdr_mde = int(scn.MyInt)
				#selection[i].name = "Mesh_"+ sName[1] +"_"+ sName[2] +"_LODx"+ str(mshHdr_lod) + "_MatID:" + str(mshHdr_matid) + "_Group:" + str(mshHdr_grp) + "_DisplayMode:" + str(mshHdr_mde)
		
		return{'FINISHED'}	  

class OBJECT_OT_UnifyVNormal(bpy.types.Operator):
	bl_idname = "unify_vnormal.selected_meshes"
	bl_label = "Unify Overlapped Vertex Normals of Selected"
 
	def execute(self, context):
		selection = context.selected_objects		
		selcnt= len (selection)	   
		# process all selected object
		for i in range(selcnt):
			mesh = selection[i].data			
			vertex_check_list = [[v.co, 0] for v in mesh.vertices]
 
			num_vert = len (vertex_check_list)
			print ("vertlist = ", vertex_check_list)
			for i in  range (num_vert):
				v1 = vertex_check_list[i]
				print( "v1 = ", v1)
				if v1[1] == 0:	# vertex 
					overlap = [i]
					for j in range( i+1, num_vert):
						v2 =  vertex_check_list[j]
						if v2[1] == 0: # vertex overlap not found yet
							if v1[0] == v2[0]:
								 v1[1] = v1[1] + 1
								 v2[1] = -1 # mark vertex processed
								 overlap.append(j)
					if v1[1] > 0:	# found overlapped vertices
						print("overlap = " , overlap)
						new_normal = mathutils.Vector([0.0,0.0,0.0])
						for v_index in overlap:
							new_normal.x += mesh.vertices[v_index].normal[0]
							new_normal.y += mesh.vertices[v_index].normal[1]
							new_normal.z += mesh.vertices[v_index].normal[2]
						new_normal *= (1.0/v1[1])  # average
						new_normal.normalize()
						print ("new normal = ", new_normal)
						for v_index in overlap:
							mesh.vertices[v_index].normal[0] = new_normal.x
							mesh.vertices[v_index].normal[1] = new_normal.y
							mesh.vertices[v_index].normal[2] = new_normal.z
			context.scene.update()				   
								
		return{'FINISHED'}	  
		
### REGISTER ###

def import_menu_func(self, context):
	self.layout.operator(IMPORT_OT_Mod.bl_idname, text="TR9 Rigged Model (.Mesh)")
	
def menu_func(self, context):
	self.layout.operator(Export_OT_Mod.bl_idname, text="TR9 Rigged Model (.Mesh)")


def register():
	bpy.utils.register_module(__name__)
	bpy.types.INFO_MT_file_import.append(import_menu_func)
	bpy.types.INFO_MT_file_export.append(menu_func)
	

def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.INFO_MT_file_import.remove(import_menu_func)	  
	bpy.types.INFO_MT_file_export.remove(menu_func)	   

if __name__ == "__main__":
	register()
	
from bpy.app.handlers import persistent	  

@persistent 
def my_handler(scene):
	#if bpy.context.mode == 'EDIT_MESH':
	print("In edit mode", scene.frame_current)
	print("===")

#bpy.app.handlers.scene_update_pre.append(my_handler)

#
#	The error message operator. When invoked, pops up a dialog 
#	window with the given message.	 
#
class MessageOperator(bpy.types.Operator):
	bl_idname = "error.message"
	bl_label = "Message"
	type = StringProperty()
	message = StringProperty()
 
	def execute(self, context):
		self.report({'INFO'}, self.message)
		print(self.message)
		return {'FINISHED'}
 
	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_popup(self, width=600, height=200)
 
	def draw(self, context):
		self.layout.label("A message has arrived")
		row = self.layout.split(0.20)
		row.prop(self, "type")
		row = self.layout.split(1.0)
		row.prop(self, "message")
		row = self.layout.split(0.80)
		row.label("") 
		row.operator("error.ok")
 
#
#	The OK button in the error dialog
#
class OkOperator(bpy.types.Operator):
	bl_idname = "error.ok"
	bl_label = "OK"
	def execute(self, context):
		return {'FINISHED'}
 
# Register
bpy.utils.register_class(OkOperator)
bpy.utils.register_class(MessageOperator)
