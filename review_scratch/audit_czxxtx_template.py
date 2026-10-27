from pathlib import Path
import struct, json, hashlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'paper_template' / '长江信息通信' / '格式核对工作_20261027'
OUT.mkdir(exist_ok=True)
P = OUT.parent / '论文格式模板 (1).doc'
u16=lambda b,o=0:struct.unpack_from('<H',b,o)[0]
u32=lambda b,o=0:struct.unpack_from('<I',b,o)[0]

class CFB:
    def __init__(self,b):
        self.b=b; self.ss=1<<u16(b,30); self.ms=1<<u16(b,32)
        ids=list(struct.unpack_from('<109I',b,76)); fids=ids[:u32(b,44)]
        self.fat=[]
        for i in fids:self.fat.extend(struct.unpack('<%dI'%(self.ss//4),self.sec(i)))
        db=self.chain(u32(b,48)); self.dirs={}
        for off in range(0,len(db),128):
            e=db[off:off+128]
            if len(e)<128:continue
            n=e[:max(0,u16(e,64)-2)].decode('utf-16le',errors='replace')
            if n:self.dirs[n]=(e[66],u32(e,116),struct.unpack_from('<Q',e,120)[0])
        r=self.dirs['Root Entry']; self.mini=self.chain(r[1])[:r[2]]
        mb=self.chain(u32(b,60)); self.mfat=list(struct.unpack('<%dI'%(len(mb)//4),mb)) if mb else []
    def sec(self,i):return self.b[(i+1)*self.ss:(i+2)*self.ss]
    def chain(self,i):
        a=[]; seen=set()
        while i<0xfffffffa and i not in seen:
            seen.add(i); a.append(self.sec(i)); i=self.fat[i]
        return b''.join(a)
    def stream(self,n):
        _,i,size=self.dirs[n]
        if size>=4096:return self.chain(i)[:size]
        a=[]; seen=set()
        while i<0xfffffffa and i not in seen:
            seen.add(i);a.append(self.mini[i*self.ms:(i+1)*self.ms]);i=self.mfat[i]
        return b''.join(a)[:size]

def sprms(b):
    ans=[]; p=0
    while p+2<=len(b):
        op=u16(b,p);p+=2;s=op>>13
        if s==6:
            if p>=len(b):break
            ln=b[p];p+=1
            if ln==255 and p+2<=len(b):ln=u16(b,p);p+=2
        else:ln={0:1,1:1,2:2,3:4,4:2,5:2,7:3}.get(s,0)
        v=b[p:p+ln];p+=ln
        ans.append({'op':hex(op),'v':v.hex(),'int':int.from_bytes(v,'little') if len(v)<=4 else None})
    return ans

def main():
    c=CFB(P.read_bytes());w=c.stream('WordDocument');t=c.stream('1Table' if u16(w,10)&0x200 else '0Table')
    p=32;csw=u16(w,p);p+=2+csw*2;cslw=u16(w,p);p+=2+cslw*4;cnt=u16(w,p);p+=2
    pairs=[(u32(w,p+i*8),u32(w,p+i*8+4)) for i in range(cnt)]
    def part(i):a,n=pairs[i];return t[a:a+n]
    cl=part(33);pos=0
    while cl[pos]==1:pos+=3+u16(cl,pos+1)
    assert cl[pos]==2
    pc=cl[pos+5:pos+5+u32(cl,pos+1)]; n=(len(pc)-4)//12; cps=[u32(pc,4*i) for i in range(n+1)];pieces=[]
    for i in range(n):
        fc=u32(pc,(n+1)*4+i*8+2);compressed=bool(fc&0x40000000);fc&=0x3fffffff
        if compressed:fc//=2
        text=w[fc:fc+(cps[i+1]-cps[i])*(1 if compressed else 2)].decode('cp1252' if compressed else 'utf-16le',errors='replace')
        pieces.append({'cp':cps[i],'end':cps[i+1],'fc':fc,'compressed':compressed,'text':text})
    fonts=[];fb=part(15);pfont=4
    for _ in range(u16(fb)):
        ln=fb[pfont]+1;r=fb[pfont:pfont+ln];pfont+=ln
        fonts.append(r[40:].decode('utf-16le',errors='replace').split('\x00')[0])
    st=part(1);cb=u16(st);cstd=u16(st,2);base=u16(st,4);stp=2+cb;styles=[]
    for idx in range(cstd):
        ln=u16(st,stp);stp+=2;r=st[stp:stp+ln];stp+=ln
        if not ln:continue
        np=base;nl=u16(r,np);np+=2;name=r[np:np+nl*2].decode('utf-16le',errors='replace');np+=nl*2+2
        if np%2:np+=1
        ups=[]
        for j in range(u16(r,4)&15):
            if np+2>len(r):break
            z=u16(r,np);np+=2;payload=r[np:np+z];np+=z+(z%2)
            ups.append({'raw':payload.hex(),'sprms':sprms(payload[2:] if (u16(r,2)&15)==1 and j==0 else payload)})
        styles.append({'index':idx,'name':name,'base':u16(r,2)>>4,'next':u16(r,4)>>4,'upx':ups})
    bins=part(12);nr=(len(bins)-4)//8;ch=[]
    for i in range(nr):
        pn=u32(bins,4*(nr+1)+i*4);fkp=w[pn*512:(pn+1)*512];cr=fkp[511]
        for j in range(cr):
            start=u32(fkp,j*4);end=u32(fkp,(j+1)*4);offs=fkp[(cr+1)*4+j]*2
            pr=fkp[offs+1:offs+1+fkp[offs]] if offs else b''
            for piece in pieces:
                step=1 if piece['compressed'] else 2
                lo=max(start,piece['fc']);hi=min(end,piece['fc']+(piece['end']-piece['cp'])*step)
                if lo<hi:
                    a=(lo-piece['fc'])//step;z=(hi-piece['fc'])//step
                    ch.append({'cp':piece['cp']+a,'text':piece['text'][a:z],'properties':sprms(pr)})
    section=[];sb=part(6);ns=(len(sb)-4)//16
    for i in range(ns):
        sed=sb[(ns+1)*4+i*12:(ns+1)*4+(i+1)*12];fc=u32(sed,2)
        if fc<0xfffffffa:section.append(sprms(w[fc+2:fc+2+u16(w,fc)]))
    bins=part(13);nr=(len(bins)-4)//8;pa=[]
    for i in range(nr):
        pn=u32(bins,4*(nr+1)+i*4);fkp=w[pn*512:(pn+1)*512];cr=fkp[511]
        for j in range(cr):
            start=u32(fkp,j*4);end=u32(fkp,(j+1)*4);offs=fkp[(cr+1)*4+j*13]*2
            if not offs:continue
            cb=fkp[offs]*2;pr=fkp[offs+1:offs+1+cb]
            if cb==0:cb=fkp[offs+1]*2;pr=fkp[offs+2:offs+2+cb]
            for piece in pieces:
                step=1 if piece['compressed'] else 2;lo=max(start,piece['fc']);hi=min(end,piece['fc']+(piece['end']-piece['cp'])*step)
                if lo<hi:
                    a=(lo-piece['fc'])//step;z=(hi-piece['fc'])//step
                    pa.append({'cp':piece['cp']+a,'text':piece['text'][a:z],'style':u16(pr),'properties':sprms(pr[2:])})
    result={'source':str(P),'sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'fonts':fonts,'styles':styles,'text':''.join(x['text'] for x in pieces),'character_runs':sorted(ch,key=lambda x:x['cp']),'paragraph_runs':sorted(pa,key=lambda x:x['cp']),'section_properties':section,'streams':c.dirs}
    (OUT/'template_binary_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'template_text.txt').write_text(result['text'],encoding='utf-8')
    print('FONTS',fonts);print('SECTIONS',section)
    for x in sorted(pa,key=lambda x:x['cp']):
        if x['cp']<1600:print({**x,'text':x['text'][:55]})

if __name__=='__main__':main()
