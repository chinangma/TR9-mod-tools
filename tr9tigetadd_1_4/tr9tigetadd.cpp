// tr9tigetadd.cpp : Defines the entry point for the console application.
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
//  TR9tigeradd - assets injector for patch.000.tiger. 
//   author : aman
//  
// Credit:  Gh0stBlade -> sharing entries format for  tiger and  drm file and his cdcEngine tools
//          - gh0stblade@live[dot]co.uk
//          
// 9-14-2023 :  add option to only patch the given drm file section with new asset, not touching other drm in tiger file 
//#include "stdafx.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#ifdef WIN32
#include <io.h>
#else
#include <unistd.h>
#endif
#pragma warning(disable : 4996)

#define TOOLS_VERSION	"1.4"

unsigned int ReadUInt(FILE* f)
{
	unsigned int v;
	fread(&v, 4, 1, f);
	return v;
}
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

// Gh0stBlade's file format documentation
struct tiger
{
	unsigned int m_magic;
	unsigned int m_version;
	unsigned int m_numVolumes;
	unsigned int m_numFiles;
	unsigned int m_flags;
	char m_srConfig[32];
};

struct tigerEntry
{
	unsigned int m_hash;
	unsigned int m_lang;
	unsigned int m_size;
	unsigned int m_offset;
};

struct drm
{
	unsigned int m_version;
	unsigned int m_nameSize;//After drmEntry1
	unsigned int m_nameSize2;//After m_nameSize
	unsigned int m_unk00;//Reserved?

	unsigned int m_unk01;//Reserved?
	unsigned int m_unk02;//Reserved?
	unsigned int m_numSections;
	unsigned int m_unk03;//Read request sections?
};

struct drmEntry
{
	unsigned int m_fileSize;		//Section size - relocationDataSize
	unsigned int m_type;			//Type of the section
	unsigned int m_relocationSize : 24;	//&0xFF000000 = numRelocations. relocationDataSize = & 0xFFFFFF00
	unsigned int m_numRelocations : 8;
	unsigned int m_hash;
	unsigned int m_lang;
};

struct drmEntry2
{
	unsigned int m_hash : 24;
	unsigned int m_type : 8;//&0xFF000000 = Type &0xFFFFFF00 = Hash
	unsigned int m_offset;//>> 4 & 0x7F should match tiger m_flags.
	unsigned int m_size;//Entire size of entry
	unsigned int m_unk00;//
};
//--end doc



bool g_bSingleDRM = false; // patch all DRM sections in tiger file by default
struct drm g_targetDRM;

// search tiger file for  a hash in offset table, replace cdrm offset and size;
void findHash(FILE* fp, FILE* log_file, unsigned int hash, unsigned int new_cdrm_offset, unsigned int new_cdrm_size, int raw_drm_size, int section_no)
{
	//read tiger header and entries (drm)
	struct tiger header;
	fread(&header, sizeof(header), 1, fp);
	struct tigerEntry* entries;

	entries = (struct tigerEntry*)malloc(sizeof(struct tigerEntry) * header.m_numFiles);
	fread(entries, sizeof(struct tigerEntry), header.m_numFiles, fp);


	char* buf[64];
	bool found = false;
	unsigned int input;
	char* pHighbyte = ((char*)&input) + 3;

	int i, j;
	int old_offset, old_size;
	struct drm drm_header;
	struct drmEntry2 drm_entry;
	for (i = 0; i < header.m_numFiles; i++)
	{
		// go to start of drm
		fseek(fp, (entries[i].m_offset & 0xffffff00) - 0x400, SEEK_SET);

		//read drm header
		fread(&drm_header, sizeof(drm_header), 1, fp);
		if (drm_header.m_version != 0x00000016)
			continue;

		if (g_bSingleDRM) // target one DRM
		{
			if (memcmp(&drm_header, &g_targetDRM, sizeof(drm_header)))
			{
				// header not match. this is not the specific DRM, skip it
				continue;
			}
		}

		long drm_header_end = ftell(fp);

		bool bFound = false;

		//printf("drm header offset %08x, %08x\n", entries[i].m_offset, drm_header.m_version);
		// put new raw file size in first section table. 
		//if ((hash >>24) == 0x0c) // if we are appending mesh file, need to update DRM offset entry to match new raw mesh file size.
		//if (raw_drm_size != 0)   // allow all asset type to specify new raw size. not all asset store file size like this. could crash game.
		{
			//printf("Search for mesh file size entry\n");
			unsigned int raw_hash = hash & 0x00ffffff;  // remove drm type name
			unsigned int raw_type = (hash >> 24) & 0xff;
			//printf("before seek %ld\n", ftell(fp));
			//printf("name, %d, name2 %d ,after seek seek %ld\n", drm_header.m_nameSize , drm_header.m_nameSize2, ftell(fp));

			for (j = 0; j < drm_header.m_numSections; j++)
			{
				// check section hash id directly 

				//fseek(fp, drm_header.m_nameSize + drm_header.m_nameSize2 + 20 * section_no , SEEK_CUR);
			
				long pos = ftell(fp);
				unsigned int file_size, file_hash, drm_offset, drm_type;
				fread(&file_size, 4, 1, fp);
				fread(&drm_type, 4, 1, fp);
				fread(&drm_offset, 4, 1, fp);
				drm_offset = (drm_offset >> 8); // lower 8 bits is num of offset entries. we need the higher 24 bits for header offset
				fread(&file_hash, 4, 1, fp);
				fseek(fp, 4, SEEK_CUR);
				if ((drm_type == raw_type) && (file_hash == raw_hash))
				{
					fflush(fp);
					fseek(fp, pos, SEEK_SET);
					// add new  mesh_size to DRM entry table
					unsigned int new_mesh_size = raw_drm_size - drm_offset;
					//printf("Asset found in first section table: section %d, name %d, name2 %d, drm_offset %x, new_asset_file_size %x, asset_body_size %x\n", j, drm_header.m_nameSize , drm_header.m_nameSize2, drm_offset, raw_drm_size, new_mesh_size);
					printf("Asset found in first section table: section %d, drm_offset %x, new_asset_file_size %x, asset_body_size %x\n", j+1, drm_offset, raw_drm_size, new_mesh_size);
					printf(" file offset: %x, change asset body size %u --> %u\n", pos, file_size, new_mesh_size);

					if (raw_drm_size != 0)
					{
						fprintf(log_file, "replace: %08x %08x %08x\n", pos, file_size, new_mesh_size);

						fwrite(&new_mesh_size, 4, 1, fp);

						fflush(fp);
						fseek(fp, 16, SEEK_CUR);
					}
					bFound = true;
					break;
				}
			}

			//printf("loop done\n");
		}

		if (!bFound) // no hash match in first section table, skip section section search
			continue;

		fseek(fp, drm_header_end + drm_header.m_numSections * 20 + drm_header.m_nameSize + drm_header.m_nameSize2, SEEK_SET);

		// look for asset reference

		for (j = 0; j < drm_header.m_numSections; j++)
		{
			int count = fread(&input, 1, 4, fp);
			if (input == hash)
			{
				long pos = ftell(fp);
				printf(" *Asset hash found in 2nd section table! at offset %x\n", pos - 4);
				fread(&old_offset, 4, 1, fp);
				fread(&old_size, 4, 1, fp);
				fprintf(log_file, "%08x %08x %08x %08x %08x\n", pos, old_offset, old_size, new_cdrm_offset, new_cdrm_size);
				fflush(fp);
				fseek(fp, pos, SEEK_SET);
				fwrite(&new_cdrm_offset, 4, 1, fp);
				fwrite(&new_cdrm_size, 4, 1, fp);
				fflush(fp);
				fseek(fp, 4, SEEK_CUR);
				break;
			}
			else
				fseek(fp, 12, SEEK_CUR);

		}

	}
	free(entries);

}


void appendCDRM(char* bigfilepath, char* drm, char* section, char* newCdrm, char* target)
{
	FILE* fdrm = fopen(drm, "rb");
	if (fdrm)
	{
		// for single drm patching, take a copy of input drm header as search target
		if (g_bSingleDRM)
		{
			fread(&g_targetDRM, sizeof(g_targetDRM), 1, fdrm);
			fseek(fdrm, 0, SEEK_SET); // move file pointer back to start of file
		}

		unsigned int version = ReadUInt(fdrm);
		unsigned int uiNameSize = ReadUInt(fdrm);
		unsigned int uiPaddingSize = ReadUInt(fdrm);
		unsigned int uiUnk00 = ReadUInt(fdrm);
		unsigned int uiUnk01 = ReadUInt(fdrm);
		unsigned int uiUnk02 = ReadUInt(fdrm);
		unsigned int uiNumSections = ReadUInt(fdrm);
		unsigned int pcd_section = atoi(section);

		if (pcd_section > uiNumSections)
		{
			printf(" invalid section number: %d\n", pcd_section);
			return;
		}
		unsigned int unk = ReadUInt(fdrm);

		// seek first section table and names, add some padding and fetch the section info in second table
		fseek(fdrm, uiNumSections * 20 + uiNameSize + uiPaddingSize + ((pcd_section - 1) * 16), SEEK_CUR);


		unsigned int uiHash = ReadUInt(fdrm);
		unsigned int ucType = (uiHash >> 24) & 0xff;
		unsigned int offset = ReadUInt(fdrm);
		unsigned int ucUnk00 = offset & 0xff;
		unsigned int uiHeaderSize = offset & 0xffffff00;
		unsigned int uiSize = ReadUInt(fdrm);
		unsigned int uiLang = ReadUInt(fdrm);
		fclose(fdrm);
		char tiger[256];
		/*
				if (ucUnk00 == 0x0)
				{
					sprintf(tiger, "%s\\title.000.tiger", bigfilepath);
					uiHeaderSize -= 0x400;
				}
				else if (ucUnk00 >= 0x10)
				{
					int fileno = (ucUnk00 >> 4) - 1;
					if (ucUnk00==0x10)
						sprintf(tiger, "%s\\patch.000.tiger", bigfilepath);
					else
						sprintf(tiger, "%s\\patch%d.000.tiger", bigfilepath, fileno);
					uiHeaderSize -= 0x400;
				}
				else
					sprintf(tiger, "%s\\bigfile.%03d.tiger", bigfilepath, ucUnk00);
		*/

		int file_id = 0x10;
		// get filanme from path
		char* target_fn = strrchr(target, '\\');
		if (!target_fn)
			target_fn = strrchr(target, '/');
		if (target_fn)
			target_fn++;
		else
			target_fn = target;
		// translate file name to file id
		if (!strcmpi(target_fn, "title.000.tiger"))
			file_id = 0x00;
		else if (!strcmpi(target_fn, "patch.000.tiger"))
			file_id = 0x10;
		else if (!strcmpi(target_fn, "patch1.000.tiger"))
			file_id = 0x20;
		else if (!strcmpi(target_fn, "patch2.000.tiger"))
			file_id = 0x30;
		else if (!strnicmp(target_fn, "patch", 5))
		{
			// assume patch file only contain single digit name
			char digit[3];
			digit[0] = target_fn[5];
			digit[1] = '\0';
			int number = atoi(digit);
			if (number > 2)
			{
				file_id = 0x10 * (number + 1);   // patch3 is 0x40
			}
			else
			{
				printf("Error: file %s not supported\n", target_fn);
				fclose(fdrm);
				return;
			}
		}
		else
		{
			printf("Cannot patch drm for %s: can only patch drm from one of the following file:\n"
				"	title.000.tiger\n"
				"	patch.000.tiger\n"
				"	patch2.000.tiger\n", target);
			fclose(fdrm);
			return;
		}
		// hard-coded to add new cdrm to patch.000.tiger
		//sprintf(tiger, "%s\\patch.%03d.tiger", bigfilepath, 000);

		// check for drm_raw_file size
		unsigned int raw_drm_size = 0;
		char* p = strrchr(newCdrm, '=');
		if (p)  // found = in file name, extract file size
		{
			*p = '\0'; // set end of file name
			p++;
			raw_drm_size = atol(p);
		}

		FILE* fpatch = fopen(target, "r+b");
		FILE* fnewCdrm = fopen(newCdrm, "rb");
		if (!fnewCdrm)
		{
			printf("Cannot open %s\n", newCdrm);
			return;
		}
		char* padding;
		if (fpatch) {
			// create log for patch uninstall
			FILE* f_log = fopen("tiger_patch.log", "wt");

			// get new cdrm file size
			fseek(fnewCdrm, 0, SEEK_END);
			long new_cdrm_size = ftell(fnewCdrm);
			fseek(fnewCdrm, 0, SEEK_SET);

			// get patch file size
			fseek(fpatch, 0, SEEK_END);
			long fsize = ftell(fpatch);

			// round up to next 2k bytes size
			long new_size = (fsize + 0x07ff) & 0xfffff800;
			int pad_size = new_size - fsize;
			if (pad_size > 0) {
				padding = new char[pad_size];
				memset(padding, 0, pad_size);
				fwrite(padding, pad_size, 1, fpatch);
				delete[] padding;
			}
			printf("append cdrm to file offset %x\n", ftell(fpatch));
			// offset in table is 0x400 greater than the actual content offset
			unsigned int new_cdrm_offset = ftell(fpatch) + 0x400;
			printf("Adjusted offset for section entry: %x, cdrm size: %x\n", new_cdrm_offset, new_cdrm_size);


			copybytes(fnewCdrm, fpatch, new_cdrm_size);
			new_size = ftell(fpatch);
			// round up to 2k and add 0x20800 bytes
			pad_size = (((new_size + 0x7ff) & 0xfffff800) + 0x20800) - new_size;
			if (pad_size > 0) {
				padding = new char[pad_size];
				memset(padding, 0, pad_size);
				fwrite(padding, pad_size, 1, fpatch);
				delete[] padding;
			}


			long patched_fsize = ftell(fpatch);
			// original and patched file size after appending new cdrm
			fprintf(f_log, "%08x %08x %s\n", fsize, patched_fsize, target_fn);

			fclose(fnewCdrm);
			fclose(fpatch);
			char targetfile[256];

			//sprintf(targetfile, "%s\\%s", bigfilepath, target);
			printf("patching all cdrm reference in file: %s\n", target);
			FILE* ftarget = fopen(target, "r+b");
			if (ftarget)
			{
				new_cdrm_offset |= file_id; // lowest order bytes is the patch fileno, 0x10 == patch.000.tiger
				findHash(ftarget, f_log, uiHash, new_cdrm_offset, new_cdrm_size, raw_drm_size, pcd_section);
				fclose(ftarget);
			}
			else
				printf("Cannot open file %s\n", targetfile);
			// close install log
			fclose(f_log);
		}
		else
			printf("Cannot open file %s\n", target);

	}
	else
		printf("Cannot open file %s\n", drm);
}

// reverse tiger patch
void removePatch(char* bigfilepath, char* install_log)
{
	FILE* f_tiger;
	FILE* f_log;

	unsigned int orig_size, patched_size;
	unsigned int orig_offset, patched_offset;
	unsigned int orig_tiger_size, patched_tiger_size, tiger_offset;

	char tiger[256], tiger_fn[256];

	tiger[0] = '\0';

	f_log = fopen(install_log, "rt");
	if (!f_log)
	{
		printf("Cannot open %s\n", install_log);
	}
	fscanf(f_log, "%08x %08x", &orig_tiger_size, &patched_tiger_size);
	// get file name
	fgets(tiger_fn, 256, f_log);

	strlwr(tiger_fn);
	char* filename;
	char* p = tiger_fn;
	// trim out leading space and newline characater
	while (*p == ' ')
		p++;
	int len = strlen(p);
	if (p[len - 1] == '\n')
		p[len - 1] = '\0';
	filename = p;
	if (!strstr(filename, "tiger"))
	{
		// invalid target file name
		// hard-coded to check patch.000.tiger
		sprintf(tiger, "%s\\%s", bigfilepath, "patch.000.tiger");
	}
	else
		sprintf(tiger, "%s\\%s", bigfilepath, filename);

	f_tiger = fopen(tiger, "r+b");
	if (!f_tiger)
	{
		printf("Cannot open %s for patch reversal\n", tiger);
		fclose(f_log);
		return;
	}

	fseek(f_tiger, 0, SEEK_END);
	long fsize = ftell(f_tiger);
	if (fsize != patched_tiger_size)
	{
		printf("%s file size does not match log file record, abort!", tiger);
		fclose(f_tiger);
	}
	else
	{
#define MAX_LINE 256
		char buf[MAX_LINE];
		// read all entry and rollback section offset/size
		while (!feof(f_log))
		{
			fgets(buf, MAX_LINE, f_log);

			if (!strncmp(buf, "replace:", 8))   // restore raw file size in first DRM section
			{
				sscanf(buf + 8, " %08x %08x %08x\n", &tiger_offset, &orig_size, &patched_size);
				fseek(f_tiger, tiger_offset, SEEK_SET);
				fflush(f_tiger);
				printf("Restore entry located at %08x: size %08x -> %08x\n", tiger_offset, patched_size, orig_size);
				fwrite(&orig_size, 4, 1, f_tiger);
				fflush(f_tiger);
			}
			else
			{
				// restore assets file id, offset and cdrm size in section drm section
				sscanf(buf, "%08x %08x %08x %08x %08x\n", &tiger_offset, &orig_offset, &orig_size, &patched_offset, &patched_size);
				fseek(f_tiger, tiger_offset, SEEK_SET);
				fflush(f_tiger);
				printf("Restore entry located at %08x: offset %08x -> %08x , size %08x -> %08x\n", tiger_offset, patched_offset, orig_offset, patched_size, orig_size);
				fwrite(&orig_offset, 4, 1, f_tiger);
				fwrite(&orig_size, 4, 1, f_tiger);
				fflush(f_tiger);
			}
		}
		fclose(f_tiger);

		// truncate tiger file ,restore to orignal size
#ifdef WIN32		
		int fd = _open(tiger, _O_BINARY | _O_RDWR);
		if (fd == -1)
			printf("cannot truncate %s to original size\n", tiger);
		else
		{
			printf("truncate %s to %d bytes\n", tiger, orig_tiger_size);
			_chsize_s(fd, orig_tiger_size);
			_close(fd);
		}
#else
		trancate(tiger, orig_tiger_size);
#endif
	}


	fclose(f_log);
}

int main(int argc, char* argv[])
{
	char* def_tiger = _strdup( "patch.000.tiger");
	if (!stricmp(argv[argc - 1], "/S"))
	{
		printf("/S option detected. Only patching one DRM file section in tiger\n");
		g_bSingleDRM = true;
		
		
	}
		
	if (argc == 3)
		removePatch(argv[1], argv[2]);
	else if (argc == 5)
		appendCDRM(argv[1], argv[2], argv[3], argv[4], def_tiger);
	else if (argc == 6)
		appendCDRM(argv[1], argv[2], argv[3], argv[4], argv[5]);
	else {
		printf("Version %s\n", TOOLS_VERSION);
		printf("TR2013 CDRM injector: Appends new cdrm(mesh/texture) to patch.000.tiger and patch affected drm sections\n"
			" To patch all drm with new asset:  %s  tiger_file_dir drm_file_path section_no cdrm_file_path<=size_before_compress> <patch.000.tiger>\n"
			" To patch just the one drm      :  %s  tiger_file_dir drm_file_path section_no cdrm_file_path<=size_before_compress> <patch.000.tiger> /S\n"
			" To remove patch  :  %s  tiger_file_dir tiger_patch.log\n", argv[0], argv[0]);
	}
	free(def_tiger);
	return 0;
}

