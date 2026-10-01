"""
EULER · calculadora de REFERÊNCIA para revisão (não é o motor nem o gerador).
Perda sensível nos gases de chaminé, base PCI, por kg de combustível seco.
Hipóteses: combustão completa; ar seco 21/79; cp constantes (1,05 gases secos; 1,90 vapor) — simplificação;
referência 25 °C; ar de combustão a 25 °C; sem umidade do ar.
"""
import numpy as np

COMP = dict(C=0.50, H=0.06, O=0.43, N=0.003, S=0.0005)   # fração mássica, base seca (cinzas 0,65%)
PCI_SECO = 18.5      # MJ/kg seco
HVAP = 2.442         # MJ/kg a 25 °C
CP_GAS, CP_H2O = 1.05e-3, 1.90e-3   # MJ/(kg·K)

def perda_gases(Tg, o2_seco, w, comp=COMP, pci_seco=PCI_SECO, Tref=25.0):
    C,H,O,N,S = (comp[k] for k in "CHONS")
    a = C/12 + H/4 + S/32 - O/32                      # kmol O2 esteq./kg seco
    y = o2_seco/100
    # (λ-1)a = y [C/12 + S/32 + (λ-1)a + 79/21 λ a + N/28]
    k = 79/21
    x = (a + y*(C/12 + S/32 + N/28) - y*a) / (1 - y - y*k)
    lam = x / a
    m_dry = (C/12)*44 + (S/32)*64 + (lam-1)*a*32 + (k*lam*a)*28 + N   # kg gás seco/kg seco
    m_h2o = 9*H + w/(1-w)
    num = (m_dry*CP_GAS + m_h2o*CP_H2O) * (Tg - Tref)
    den = pci_seco - HVAP*w/(1-w)
    return num/den, lam

if __name__ == "__main__":
    q, lam = perda_gases(180, 8, 0.40)
    print(f"referência 180 °C, O2 8%, w 40%: perda = {q*100:.2f}%  λ = {lam:.3f}")
