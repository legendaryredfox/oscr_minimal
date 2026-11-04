# SPDX-License-Identifier: GPL-3.0-or-later
import re, uuid, sys
p=sys.argv[1]
s=open(p).read()
assert '"C5"' not in s and 'Connector:TestPoint' not in s, "ja aplicado"

def block_at(s, start):
    d=0;j=start
    while True:
        c=s[j]
        if c=='(':d+=1
        elif c==')':
            d-=1
            if d==0:break
        j+=1
    return s[start:j+1], j+1

# --- embutir o simbolo TestPoint ---
stock=open('/usr/share/kicad/symbols/Connector.kicad_sym').read()
i=stock.index('(symbol "TestPoint"')
tp,_=block_at(stock,i)
tp=tp.replace('(symbol "TestPoint"','(symbol "Connector:TestPoint"',1)
tp='\t\t'+tp.replace('\n','\n') + '\n'   # ja vem com 2 tabs nas linhas internas
li=s.index('\t(lib_symbols')
lb,lend=block_at(s,li+1)
close=lend-1                                # posicao do ')' que fecha lib_symbols
s=s[:close].rstrip('\t')+tp+'\t)'+s[lend:]

# --- clonar C3 em C5 e C6 ---
ci=s.index('\t(symbol\n\t\t(lib_id "Device:C")\n\t\t(at 1040.13 480.06 0)')
c3,_=block_at(s,ci+1)
c3='\t'+c3+'\n'
def clone(txt, ref, dx):
    def sh(m):
        x=float(m.group(1))+dx
        return '(at %s %s%s)'%(('%.3f'%x).rstrip('0').rstrip('.'),m.group(2),m.group(3) or '')
    t=re.sub(r'\(at ([0-9.]+) ([0-9.]+)( \d+)?\)',sh,txt)
    t=re.sub(r'\(uuid "[^"]*"\)',lambda m:'(uuid "%s")'%uuid.uuid4(),t)
    t=t.replace('"Reference" "C3"','"Reference" "%s"'%ref).replace('(reference "C3")','(reference "%s")'%ref)
    return t
new=''
labels=''
def label(name,x,y,ang,just):
    return '\t(label "%s"\n\t\t(at %s %s %d)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify %s)\n\t\t)\n\t\t(uuid "%s")\n\t)\n'%(name,x,y,ang,just,uuid.uuid4())
for ref,x in (("C5",1080.77),("C6",1101.09)):
    new+=clone(c3,ref,x-1040.13)
    labels+=label('+5V',x,476.25,90,'left bottom')+label('GND',x,483.87,270,'right bottom')

# --- pontos de teste ---
def tpblock(ref,val,x,y):
    u=lambda: uuid.uuid4()
    def prop(name,v,dx,dy,hide=False):
        return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s 0)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n%s\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify left)\n\t\t\t)\n\t\t)\n'
                %(name,v,x+dx,y+dy,'\t\t\t(hide yes)\n' if hide else ''))
    return ('\t(symbol\n\t\t(lib_id "Connector:TestPoint")\n\t\t(at %s %s 0)\n\t\t(unit 1)\n\t\t(body_style 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n\t\t(uuid "%s")\n'%(x,y,u())
        +prop('Reference',ref,2.54,-1.27)+prop('Value',val,2.54,1.27)
        +prop('Footprint','TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm',0,0,True)
        +prop('Datasheet','',0,0,True)+prop('Description','test point',0,0,True)
        +'\t\t(pin "1"\n\t\t\t(uuid "%s")\n\t\t)\n'%u()
        +'\t\t(instances\n\t\t\t(project "dumper"\n\t\t\t\t(path "/7a60289e-82cc-4290-bd86-3bc08aff2373"\n\t\t\t\t\t(reference "%s")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n'%ref)
tps=[("TP1","+5V","5V"),("TP2","GND","GND"),("TP3","D6","/CE"),("TP4","D9","/OE"),("TP5","D8","/WE"),("TP6","D7","/UWR")]
for k,(ref,net,val) in enumerate(tps):
    x=round(1019.81+20.32*k,2); y=520.7
    new+=tpblock(ref,"TP "+val,x,y)
    labels+=label(net,x,y,90,'left bottom')
i=s.index('\t(label "')          # os simbolos ficam antes do primeiro rotulo
s=s[:i]+new+s[i:]
j=s.index('\t(sheet_instances')
s=s[:j]+labels+s[j:]
open(p,'w').write(s)
print("ok")
