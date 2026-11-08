# megadrive_sms — componentes que podem ser retirados e o que se perde

Placa Mega Drive + Master System (`boards/megadrive_sms/`): dois slots, LED e capacitores. Não tem Si5351, PIC, regulador de 3,3 V, R2 nem bloco de troca de cartucho.

> **Nada aqui foi testado em hardware.** Conclusões vêm de `pinmap.md` e do firmware (`firmware/oscr/src/cores/MegaDrive.cpp`; o núcleo `SMS.cpp` do OSCR não usa clock e está ligado no fork desde a D137).

| Peça | Retirar? | O que deixa de funcionar | Cartuchos afetados |
|---|---|---|---|
| **D1** LED + **R1** 220 Ω | Sim | Some a indicação de atividade (D38) | Nenhum |
| **TP1 a TP6** pontos de teste | Sim | Só o acesso para medir `/UWR`, `/CE`, `5V`, `GND`, `/OE`, `/WE` | Nenhum |
| **C2, C3, C4** 100 nF (slot Mega Drive) | Não recomendado | Desacoplamento do cartucho; sem eles, ruído pode dar leitura errada | Mais provável nos de ROM grande |
| **C5** 100 nF (slot SMS) | Não recomendado | Desacoplamento do cartucho de Master System | Todos os do SMS |
| **C1** 470 µF | Não recomendado | Reserva de carga do 5 V; sem ela, picos podem reiniciar o Mega | Todos |

Não há chip opcional. O pino 47 (Clock) do slot SMS fica sem ligação (D136); se algum cartucho exigir o clock do console, só um adaptador com o sinal resolve.
