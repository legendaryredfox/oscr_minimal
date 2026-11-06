# third_party: código do sd2snes (GPL v2 only)

Arquivos copiados sem alteração de `https://github.com/mrehkopf/sd2snes`, pasta `cic/`, no commit
`fead36fec2f1b5ef6e6aae0685afd0a46fac63b2` (2026-10-23):

| Arquivo | Para quê |
|---|---|
| `snescic-lock-resync.asm` / `.hex` | CIC "lock" com resincronização e detecção da região do key (o mesmo `.hex` que o OSCR manda gravar no PIC12F629). Roda no RP2040 pelo interpretador. |
| `snescic-key.asm` | CIC "key" (cartucho). Só entra nos testes de PC: o simulador liga o lock a ele. |
| `snescic-lock.asm` | Versão do lock sem resincronização; só referência. |

Licença: cabeçalho dos arquivos ("GNU General Public License ... version 2 of the License only"; o
repositório do sd2snes declara GPL-2.0). Como é "v2 only", **não misture estes arquivos com o código
GPL v3 do firmware do OSCR num mesmo programa**. Aqui o RP2040 roda um programa separado, em outro chip,
e `firmware/cic_rp2040/` fica sob GPL v2 (só) por conter o `.hex` do lock. Mantenha os avisos de copyright.

`test/Makefile` monta o `.asm` com o `gpasm` e confere que o resultado é idêntico ao `.hex` distribuído.
