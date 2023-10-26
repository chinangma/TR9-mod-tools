// dds2pcd9.cpp : This file contains the 'main' function. Program execution begins and ends there.
//

#include <iostream>

// tr9pcd9patch.cpp : Defines the entry point for the console application.
//
/*

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/
//  tr9pcd9patch - take a pcd9 texture and replace its content with a DDS file of the same resoultion and pixel format. 
//   author : aman
//  
// Credit:  Gh0stBlade -> for sharing enteies format for  tiger and  drm file and his cdcEngine tools
//          - gh0stblade@live[dot]co.uk
//          
//
#include <stdio.h>
#include <string.h>
#include "d3d.h"
#include <dxgiformat.h>
#include <wchar.h>
#pragma warning(disable : 4996)
typedef unsigned int uint32;
#pragma pack(push, 1)

#define DDS_MAGIC 0x20534444 // "DDS "
#define PCD9_MAGIC 0x39444350 //"PCD9"

struct DDS_PIXELFORMAT
{
	uint32  size;
	uint32  flags;
	uint32  fourCC;
	uint32  RGBBitCount;
	uint32  RBitMask;
	uint32  GBitMask;
	uint32  BBitMask;
	uint32  ABitMask;
};

#define DDS_FOURCC      0x00000004  // DDPF_FOURCC
#define DDS_RGB         0x00000040  // DDPF_RGB
#define DDS_RGBA        0x00000041  // DDPF_RGB | DDPF_ALPHAPIXELS
#define DDS_LUMINANCE   0x00020000  // DDPF_LUMINANCE
#define DDS_LUMINANCEA  0x00020001  // DDPF_LUMINANCE | DDPF_ALPHAPIXELS
#define DDS_ALPHA       0x00000002  // DDPF_ALPHA
#define DDS_PAL8        0x00000020  // DDPF_PALETTEINDEXED8

#define DDS_HEADER_FLAGS_TEXTURE        0x00001007  // DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT
#define DDS_HEADER_FLAGS_MIPMAP         0x00020000  // DDSD_MIPMAPCOUNT
#define DDS_HEADER_FLAGS_VOLUME         0x00800000  // DDSD_DEPTH
#define DDS_HEADER_FLAGS_PITCH          0x00000008  // DDSD_PITCH
#define DDS_HEADER_FLAGS_LINEARSIZE     0x00080000  // DDSD_LINEARSIZE

#define DDS_HEIGHT 0x00000002 // DDSD_HEIGHT
#define DDS_WIDTH  0x00000004 // DDSD_WIDTH

#define DDS_SURFACE_FLAGS_TEXTURE 0x00001000 // DDSCAPS_TEXTURE
#define DDS_SURFACE_FLAGS_MIPMAP  0x00400008 // DDSCAPS_COMPLEX | DDSCAPS_MIPMAP
#define DDS_SURFACE_FLAGS_CUBEMAP 0x00000008 // DDSCAPS_COMPLEX

#define DDS_CUBEMAP_POSITIVEX 0x00000600 // DDSCAPS2_CUBEMAP | DDSCAPS2_CUBEMAP_POSITIVEX
#define DDS_CUBEMAP_NEGATIVEX 0x00000a00 // DDSCAPS2_CUBEMAP | DDSCAPS2_CUBEMAP_NEGATIVEX
#define DDS_CUBEMAP_POSITIVEY 0x00001200 // DDSCAPS2_CUBEMAP | DDSCAPS2_CUBEMAP_POSITIVEY
#define DDS_CUBEMAP_NEGATIVEY 0x00002200 // DDSCAPS2_CUBEMAP | DDSCAPS2_CUBEMAP_NEGATIVEY
#define DDS_CUBEMAP_POSITIVEZ 0x00004200 // DDSCAPS2_CUBEMAP | DDSCAPS2_CUBEMAP_POSITIVEZ
#define DDS_CUBEMAP_NEGATIVEZ 0x00008200 // DDSCAPS2_CUBEMAP | DDSCAPS2_CUBEMAP_NEGATIVEZ

#define DDS_CUBEMAP_ALLFACES (DDS_CUBEMAP_POSITIVEX | DDS_CUBEMAP_NEGATIVEX |\
                              DDS_CUBEMAP_POSITIVEY | DDS_CUBEMAP_NEGATIVEY |\
                              DDS_CUBEMAP_POSITIVEZ | DDS_CUBEMAP_NEGATIVEZ)

#define DDS_CUBEMAP 0x00000200 // DDSCAPS2_CUBEMAP

#define DDS_FLAGS_VOLUME 0x00200000 // DDSCAPS2_VOLUME

typedef struct
{
	uint32          size;
	uint32          flags;
	uint32          height;
	uint32          width;
	uint32          pitchOrLinearSize;
	uint32          depth; // only if DDS_HEADER_FLAGS_VOLUME is set in flags
	uint32          mipMapCount;
	uint32          reserved1[11];
	DDS_PIXELFORMAT ddspf;
	uint32          caps;
	uint32          caps2;
	uint32          caps3;
	uint32          caps4;
	uint32          reserved2;
} DDS_HEADER;

typedef struct
{
	DXGI_FORMAT dxgiFormat;
	uint32      resourceDimension;
	uint32      miscFlag; // See D3D11_RESOURCE_MISC_FLAG
	uint32      arraySize;
	uint32      reserved;
} DDS_HEADER_DXT10;

#pragma pack(pop)

struct PCD9HEADER {
	int magic;
	int format;
	int datasize;
	int num_mipmap;   // this is always set to 2  for TR2013. The data section can still have more than 2 mipmap, will not cause any issue.
	short width, height;
	//unsigned short bpp, num_mipmap;
	short unk;  // 0x0001
	byte unk_1;
	byte size_shift;  // the log2() of the width or height, which ever is smaller 
	short unk2; // 0x0007
	short flags;  //  0x04 for normal map, 0x01 for everything else 
} pcd9header;

char buffer[4096];
void copybytes(FILE* src, FILE* dst, unsigned int size)
{
	unsigned int len;
	while (size > 0)
	{
		if (size > 4096)
			len = 4096;
		else
			len = size;
		fread(buffer, len, 1, src);
		fwrite(buffer, len, 1, dst);
		size -= len;
	}
}

void patch( char* dds, int pcd_flags)
{
	{
		FILE* dds_f = fopen(dds, "rb");
		if (!dds_f)
		{
			printf("cannot find file: %s\n", dds);
			return;
		}
		uint32 dds_magic;
		DDS_HEADER ddsheader;
		fread(&dds_magic, 4, 1, dds_f);
		fread(&ddsheader, sizeof(ddsheader), 1, dds_f);
		fseek(dds_f, 0, SEEK_END);
		int datasize = ftell(dds_f) - 0x80;
		
		pcd9header.magic = PCD9_MAGIC;
		pcd9header.format = ddsheader.ddspf.fourCC;
		pcd9header.datasize = datasize;
		pcd9header.num_mipmap = 2;// ddsheader.mipMapCount;
		pcd9header.width = ddsheader.width;
		pcd9header.height = ddsheader.height;
		pcd9header.unk = 0x0001;
		pcd9header.size_shift = (ddsheader.width < ddsheader.height) ? log2(ddsheader.width) : log2(ddsheader.height);
		pcd9header.unk2 = 0x0007;
		pcd9header.flags = pcd_flags; // default to 0x1 for texture


		char out[1024];
		char* p = strrchr(dds, '\\');
		if (p)
		{
			dds = p + 1;   // cut out file path
		}
		else
		{
			strrchr(dds, '/');
			if (p)
				dds = p + 1; // cut  out file path
		}
		p = strrchr(dds, '.');
				if (p)  *p = 0;  // cut out file extension
		

		strcpy(out, dds);
		strcat(out, ".pcd9");
		FILE* out_f = fopen(out, "wb");
		if (!out_f)
		{
			printf("Failed to write to pcd9 file\n");
		}
		else
		{
			fwrite(&pcd9header, sizeof(pcd9header), 1, out_f);
			fseek(dds_f, 0x80, SEEK_SET); // skip dds header
				// copy dds mipmaps. it is modder's resposibility to provide DDS with matching DXT type and resolution for PCD9 texture patching.
			copybytes(dds_f, out_f, pcd9header.datasize);
			fclose(out_f);
		}
		fclose(dds_f);
	}
}

int main(int argc, char* argv[])
{
	if (argc < 2)
		printf("TR2013 DDS to pcd9 texture converter. flags is optional, set it to 4 if dds_file is a normal map\n"
			"Usage: %s dds_file  <flags>\n", argv[0]);
					
	else
	{
		if (argc > 2)
			patch(argv[1], atoi(argv[2]));
		else
			patch(argv[1],0x0001);
	}
	return 0;
}
