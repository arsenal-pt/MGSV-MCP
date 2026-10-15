"""Real MCP protocol calls and synthetic converter round trips; no game assets."""
import asyncio
import json
import hashlib
import struct
import sys
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client,StdioServerParameters
from mgsv_mcp.config import Config
from mgsv_mcp import workbench


async def protocol():
    params=StdioServerParameters(command=sys.executable,args=[str(ROOT/"server.py")])
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as client:
            result=await client.initialize()
            tools=await client.list_tools()
            assert len(tools.tools)>=22
            for name,args in [("server_status",{}),("search",{"query":"TppRouteSet"}),
                              ("fetch",{"id":"wiki/GzsTool.md"}),
                              ("list_modding_tools",{"query":"File Monolith"}),
                              ("modding_workflow",{"topic":"textures"}),
                              ("wiki_assets",{"query":"Export_Symbols"}),
                              ("search_wiki",{"query":"StaticModel","kind":"entity"}),
                              ("hash_game_path",{"value":"/Assets/tpp/test.txt"})]:
                call=await client.call_tool(name,args)
                assert not call.is_error,(name,call)
            invalid=await client.call_tool("read_wiki_page",{"page":"../../secret"})
            assert invalid.is_error
            resources=await client.list_resources()
            assert len(resources.resources)==2
            await client.read_resource("mgsv://status")
            prompts=await client.list_prompts()
            assert len(prompts.prompts)==1
            await client.get_prompt("research_mod",{"idea":"custom textures"})
            return {"server":result.server_info.name,"tools":len(tools.tools),"resources":len(resources.resources),"prompts":len(prompts.prompts),"invalid_input":"error returned"}


def roundtrips():
    c=Config()
    fixture=c.workspace/("verification-"+uuid.uuid4().hex[:8]);fixture.mkdir(parents=True)
    # LANG v3 with two original strings. Header and keys follow the upstream parser.
    values=struct.pack("<h",0)+b"MCP synthetic test\0"+struct.pack("<h",1)+"Second entry: café".encode()+b"\0"
    second=2+len(b"MCP synthetic test\0")
    values+=b"\0"*((-len(values))%4)
    original=struct.pack("<6I",0x474e414c,3,0x454c,2,24,24+len(values))+values+struct.pack("<4I",12345,0,54321,second)
    lng=fixture/"synthetic.lng2";lng.write_bytes(original)
    job=workbench.prepare(c,"langtool",str(lng));result=workbench.run(c,job["job_id"])
    assert result["state"]=="completed",result
    xml=Path(result["job_path"])/"input/synthetic.lng2.xml"
    assert "MCP synthetic test" in xml.read_text(encoding="utf-8-sig")
    job2=workbench.prepare(c,"langtool",str(xml),str(xml.parent));result2=workbench.run(c,job2["job_id"])
    rebuilt=Path(result2["job_path"])/"input/synthetic.lng2"
    assert rebuilt.read_bytes()==original
    assert lng.read_bytes()==original
    # One 4x4 DXT1 block; a valid synthetic DDS fixture without game content.
    header=[124,0x81007,4,4,8,0,1]+[0]*11+[32,4,struct.unpack("<I",b"DXT1")[0],0,0,0,0,0]+[0x1000,0,0,0,0]
    dds=fixture/"synthetic.dds";pixels=struct.pack("<HHI",0xf800,0,0)
    dds.write_bytes(b"DDS "+struct.pack("<31I",*header)+pixels)
    job3=workbench.prepare(c,"ftextool",str(dds));result3=workbench.run(c,job3["job_id"])
    assert result3["state"]=="completed",result3
    ftex=Path(result3["job_path"])/"input/synthetic.ftex"
    assert ftex.read_bytes().startswith(b"FTEX")
    job4=workbench.prepare(c,"ftextool",str(ftex));result4=workbench.run(c,job4["job_id"])
    rebuilt_dds=Path(result4["job_path"])/"input/synthetic.dds"
    assert rebuilt_dds.read_bytes()[-8:]==pixels
    archive_jobs=archive_roundtrip(c,fixture)
    return {"lang":"binary -> XML -> byte-identical binary","texture":"DDS -> FTEX/FTEXS -> DDS preserves compressed pixel block","archive":"FPK -> files/XML -> byte-identical FPK; original payload recovered","source_inputs":"unchanged","jobs":[x["job_id"] for x in [job,job2,job3,job4]]+archive_jobs}


def archive_roundtrip(c,fixture):
    name=b"/Assets/tpp/mcp_test.txt";payload=b"Original synthetic MCP payload\n"
    names=name+b"\0";names+=b"\0"*((-len(names))%16)
    data_offset=96+len(names)
    data=payload+b"\0"*((-len(payload))%16)
    header=b"foxfpk\0win"+struct.pack("<I",data_offset+len(data))+b"\0"*18+struct.pack("<III",2,1,0)+b"\0"*4
    entry=struct.pack("<8I",data_offset,0,len(payload),0,96,0,len(name),0)+hashlib.md5(name).digest()
    original=header+entry+names+data
    path=fixture/"synthetic.fpk";path.write_bytes(original)
    unpack=workbench.prepare(c,"gzstool",str(path));result=workbench.run(c,unpack["job_id"])
    assert result["state"]=="completed",result
    root=Path(result["job_path"])/"input"
    assert (root/"synthetic_fpk/Assets/tpp/mcp_test.txt").read_bytes()==payload
    repack=workbench.prepare(c,"gzstool",str(root/"synthetic.fpk.xml"),str(root));result2=workbench.run(c,repack["job_id"])
    assert result2["state"]=="completed",result2
    assert (Path(result2["job_path"])/"input/synthetic.fpk").read_bytes()==original
    assert path.read_bytes()==original
    return [unpack["job_id"],repack["job_id"]]


if __name__=="__main__":
    result={"protocol":asyncio.run(protocol()),"roundtrips":roundtrips()}
    (ROOT/"data/verification.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
