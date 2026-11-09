import struct, json, sys
def read_dbf(path):
    f=open(path,'rb').read(); n=struct.unpack('<I',f[4:8])[0]; hl=struct.unpack('<H',f[8:10])[0]; rl=struct.unpack('<H',f[10:12])[0]
    fields=[]; p=32
    while f[p]!=0x0D:
        name=f[p:p+11].split(b'\0')[0].decode(); ln=f[p+16]; fields.append((name,ln)); p+=32
    recs=[]
    for i in range(n):
        r=f[hl+i*rl:hl+(i+1)*rl]; o=1; d={}
        for name,ln in fields: d[name]=r[o:o+ln].decode('latin-1').strip(); o+=ln
        recs.append(d)
    return recs
def read_shp(path):
    f=open(path,'rb').read(); p=100; shapes=[]
    while p<len(f):
        clen=struct.unpack('>I',f[p+4:p+8])[0]*2; c=f[p+8:p+8+clen]; p+=8+clen
        st=struct.unpack('<i',c[:4])[0]
        if st==0: shapes.append(None); continue
        nparts,npts=struct.unpack('<ii',c[36:44]); parts=list(struct.unpack('<%di'%nparts,c[44:44+4*nparts]))
        pts=struct.unpack('<%dd'%(2*npts),c[44+4*nparts:44+4*nparts+16*npts])
        pts=[(round(pts[2*i],3),round(pts[2*i+1],3)) for i in range(npts)]
        rings=[pts[s:e] for s,e in zip(parts,parts[1:]+[npts])]
        shapes.append(rings)
    return shapes
def ring_area(r): return sum(x1*y2-x2*y1 for (x1,y1),(x2,y2) in zip(r,r[1:]+r[:1]))/2
def to_geom(rings):
    # shapefile: outer rings clockwise (negative area in this formula), holes counter-clockwise
    polys=[]
    for r in rings:
        # drop consecutive duplicates after rounding
        rr=[r[0]]+[q for a,q in zip(r,r[1:]) if q!=a]
        if len(rr)<4: continue
        if ring_area(rr)<0: polys.append([[list(x) for x in rr]])   # outer ring, clockwise as d3-geo expects
        elif polys: polys[-1].append([list(x) for x in rr])          # hole, counter-clockwise
    return {'type':'MultiPolygon','coordinates':polys}
def convert(base, keep):
    recs=read_dbf(base+'.dbf'); shps=read_shp(base+'.shp'); feats=[]
    for r,s in zip(recs,shps):
        if s is None: continue
        feats.append({'type':'Feature','properties':{k:r[k] for k in keep},'geometry':to_geom(s)})
    return {'type':'FeatureCollection','features':feats}
