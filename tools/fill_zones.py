# Preenche as zonas de cobre fora do MCP (o refill do MCP via SWIG pode travar).
# Uso: ~/development/llms/KiCAD-MCP-Server/.venv/bin/python tools/fill_zones.py hardware/dumper.kicad_pcb
import pcbnew, sys
p=sys.argv[1]
b=pcbnew.LoadBoard(p)
z=b.Zones()
print('zones',len(z))
for zz in z: print(zz.GetNetname(), b.GetLayerName(zz.GetLayer()), zz.GetPadConnection(), zz.GetMinThickness()/1e6, zz.GetLocalClearance()/1e6)
pcbnew.ZONE_FILLER(b).Fill(z)
pcbnew.SaveBoard(p,b)
print('filled')
