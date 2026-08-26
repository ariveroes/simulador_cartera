"""
TEST LOCAL - Simula datos para probar la app sin Google Sheets
Útil para desarrollo y testing de UI
"""

import pandas as pd
import os

# Datos simulados (copia de 5 proyectos del Sheet)
PROYECTOS_SIMULADOS = [
    {
        'ID': 'SVQ-1',
        'Nombre': 'Sevilla 1',
        'ESTADO': 'CERRADO',
        'Ubicación': 'España',
        'Tipología de Dividendo': 'rendimientos mensuales + final',
        'Importe proyecto en €': 54800,
        'Importe proyecto en $': 64000,
        'Estimación Nº Meses desde Lanzamiento': 45,
        'Nº Meses restantes de renta hasta Estimacion fin': 2,
        'Estimación Rentab. Rendim. Recurr. anualizados Reentel': 0.1101,
        'Estimación Rentab. Plusvalía Reentel': 0.0692,
        'Estimación Rentab. Total (Alq. + Plusv.) anualizado Reentel': 0.1447,
        'Estimación Rentab. Rendim. Recurr. anualizados RP': 0.1101,
        'Estimación Rentab. Plusvalía RP': 0.0692,
        'Estimación Rentab. Total (Alq. + Plusv.) anualizado RP': 0.1447,
        'Estimación Rentab. Rendim. Recurr. anualizados SR': 0.1101,
        'Estimación Rentab. Plusvalía SR': 0.0692,
        'Estimación Rentab. Total (Alq. + Plusv.) anualizado SR': 0.1447,
    },
    {
        'ID': 'GND-1',
        'Nombre': 'Gandia 1',
        'ESTADO': 'CERRADO',
        'Ubicación': 'España',
        'Tipología de Dividendo': 'rendimientos mensuales + final',
        'Importe proyecto en €': 46000,
        'Importe proyecto en $': 53662,
        'Estimación Nº Meses desde Lanzamiento': 50,
        'Nº Meses restantes de renta hasta Estimacion fin': 4,
        'Estimación Rentab. Rendim. Recurr. anualizados Reentel': 0.1000,
        'Estimación Rentab. Plusvalía Reentel': 0.0744,
        'Estimación Rentab. Total (Alq. + Plusv.) anualizado Reentel': 0.1372,
        'Estimación Rentab. Rendim. Recurr. anualizados RP': 0.1000,
        'Estimación Rentab. Plusvalía RP': 0.0744,
        'Estimación Rentab. Total (Alq. + Plusv.) anualizado RP': 0.1372,
        'Estimación Rentab. Rendim. Recurr. anualizados SR': 0.1000,
        'Estimación Rentab. Plusvalía SR': 0.0744,
        'Estimación Rentab. Total (Alq. + Plusv.) anualizado SR': 0.1372,
    },
    {
        'ID': 'MIA-1',
        'Nombre': 'Miami 1',
        'ESTADO': 'EN EXPLOTACIÓN',
        'Ubicación': 'USA',
        'Tipología de Dividendo': 'rendimientos mensuales + final',
        'Importe proyecto en €': 75000,
        'Importe proyecto en $': 87500,
        'Estimación Nº Meses desde Lanzamiento': 8,
        'Nº Meses restantes de renta hasta Estimacion fin': 28,
        'Estimación Rentab. Rendim. Recurr. anualizados Reentel': 0.1200,
        'Estimación Rentab. Plusvalía Reentel': 0.0850,
        'Estimación Rentab. Total (Alq. + Plusv.) anualizado Reentel': 0.1580,
        'Estimación Rentab. Rendim. Recurr. anualizados RP': 0.1400,
        'Estimación Rentab. Plusvalía RP': 0.0950,
        'Estimación Rentab. Total (Alq. + Plusv.) anualizado RP': 0.1820,
        'Estimación Rentab. Rendim. Recurr. anualizados SR': 0.1600,
        'Estimación Rentab. Plusvalía SR': 0.1050,
        'Estimación Rentab. Total (Alq. + Plusv.) anualizado SR': 0.2020,
    },
    {
        'ID': 'MEX-1',
        'Nombre': 'Ciudad de México 1',
        'ESTADO': 'EN REFORMA',
        'Ubicación': 'México',
        'Tipología de Dividendo': 'rendimientos trimestrales + final',
        'Importe proyecto en €': 60000,
        'Importe proyecto en $': 70000,
        'Estimación Nº Meses desde Lanzamiento': 3,
        'Nº Meses restantes de renta hasta Estimacion fin': 21,
        'Estimación Rentab. Rendim. Recurr. anualizados Reentel': 0.1100,
        'Estimación Rentab. Plusvalía Reentel': 0.0800,
        'Estimación Rentab. Total (Alq. + Plusv.) anualizado Reentel': 0.1500,
        'Estimación Rentab. Rendim. Recurr. anualizados RP': 0.1300,
        'Estimación Rentab. Plusvalía RP': 0.0950,
        'Estimación Rentab. Total (Alq. + Plusv.) anualizado RP': 0.1750,
        'Estimación Rentab. Rendim. Recurr. anualizados SR': 0.1500,
        'Estimación Rentab. Plusvalía SR': 0.1100,
        'Estimación Rentab. Total (Alq. + Plusv.) anualizado SR': 0.2000,
    },
    {
        'ID': 'BUE-1',
        'Nombre': 'Buenos Aires 1',
        'ESTADO': 'FINANCIÁNDOSE',
        'Ubicación': 'Argentina',
        'Tipología de Dividendo': 'rendimientos mensuales + final',
        'Importe proyecto en €': 55000,
        'Importe proyecto en $': 64167,
        'Estimación Nº Meses desde Lanzamiento': 1,
        'Nº Meses restantes de renta hasta Estimacion fin': 23,
        'Estimación Rentab. Rendim. Recurr. anualizados Reentel': 0.1250,
        'Estimación Rentab. Plusvalía Reentel': 0.0900,
        'Estimación Rentab. Total (Alq. + Plusv.) anualizado Reentel': 0.1650,
        'Estimación Rentab. Rendim. Recurr. anualizados RP': 0.1450,
        'Estimación Rentab. Plusvalía RP': 0.1050,
        'Estimación Rentab. Total (Alq. + Plusv.) anualizado RP': 0.1920,
        'Estimación Rentab. Rendim. Recurr. anualizados SR': 0.1700,
        'Estimación Rentab. Plusvalía SR': 0.1200,
        'Estimación Rentab. Total (Alq. + Plusv.) anualizado SR': 0.2200,
    }
]

def crear_df_prueba():
    """Crea DataFrame con datos simulados"""
    return pd.DataFrame(PROYECTOS_SIMULADOS)

if __name__ == "__main__":
    df = crear_df_prueba()
    print("Datos de prueba cargados:")
    print(df[['ID', 'Nombre', 'Ubicación', 'Importe proyecto en €']].to_string())
    print(f"\nTotal: {len(df)} proyectos simulados")
