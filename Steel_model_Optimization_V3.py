# -*- coding: utf-8 -*-
"""
Created on Mon Feb 21 16:30:30 2022

@author: Otto

Steel - Energy and Emissions simulator

R1 = Route BOF using Coal
R2 = Route BOF using Charcoal
R3 = Route EAF using scrap
R4 = Route Independet producers 

FALTA:
    FEITO: -  Ajustar medidas de mitigação nas etapas corretas
    FEITO: --Fazer a lista: Route-> MM -> infos (faço isso com o transpose)
    - VERIFICAR O CALCULO DAS EMISSOES (valor diferente com planilhas do excel)
        - conferir fator de emissão
    -anualizar o capex
    -capex Carvão vegetal
    ----->CAPEX CC  https://www.infomoney.com.br/negocios/destaque-esg-aco-verde-do-brasil-ganha-espaco-no-mercado-de-capitais/
    -adicionar economia dos combustíveis
        -Conferir as unidades da economia dos combustíveis
RESOLVIDO: 22/07 - tá dando uma diferença pequena entre as minhas emissões calculadas na função e as emissões calculadas na otimização.
22/07 - Colocar custos em dólar;
22/07 - verificar se os capex estão em comparativo;
25/07 - Colocar CAPEX das Routes tradicionais; 
08/08 - Ajustar a penetração das medidas. tá dando uma eficiência alta (4.5Gj ou 20%)
"""
 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pyomo.environ import *

#%%
"""1. Importing Data"""

#Confersion factor Gj to Ktoe    
tj_to_ktoe = 1/41.868
ktoe_to_tj = 41.868

#Greenhouse gases Global Warning Potential GWP:
GWP = {'CH4':28,'N2O':265}

"""Importing Crude Steel production by route in kt"""

steel_production = pd.read_csv("https://raw.githubusercontent.com/ottohebeda/Iron-and-steel-model/main/steel_production.csv") #in kt
steel_production = steel_production.set_index('Year')   
steel_production['Total']= steel_production.sum(axis=1)

"""Importing Pig Iron production by Route in kt"""
pig_iron_production = pd.read_csv("https://raw.githubusercontent.com/ottohebeda/Iron-and-steel-model/main/Pig_iron_production.csv")
pig_iron_production = pig_iron_production.set_index('Ano')
pig_iron_production['Share BOF CC'] = pig_iron_production['Integrada CV']/(pig_iron_production['Integrada CV']+pig_iron_production['Integrada CM'])
pig_iron_production['Share BOF MC']=1-pig_iron_production['Share BOF CC']

"""Charcoal and coal in BF-BOF production"""
#BOF Coal production in Mt
steel_production['BOF MC'] = steel_production.BOF*pig_iron_production['Share BOF MC']

#BOF Charcoal production in Mt
steel_production['BOF CC'] = steel_production.BOF*pig_iron_production['Share BOF CC']

steel_production['Total']= steel_production['BOF']+steel_production['EAF'] #Removing EOF from the total
steel_production = steel_production.drop('EOF',axis= 'columns')

steel_production['Share_BOF_MC'] = steel_production['BOF MC']/steel_production['Total']
steel_production['Share_BOF_CC'] = steel_production['BOF CC']/steel_production['Total']
steel_production['Share_EAF'] = steel_production['EAF']/steel_production['Total']

"""Importing Emission Factor"""
emission_factor = pd.read_csv("https://raw.githubusercontent.com/ottohebeda/Iron-and-steel-model/main/emission_factor.csv") #t/TJ or kg/GJ
emission_factor = emission_factor.set_index('Combustivel')
emission_factor['CO2e'] = emission_factor['CO2'] + emission_factor['CH4']*28 + emission_factor['N2O']*265

"""Importing Energy Consumption compatible with the Useful Energy Balance (BEU):
    In the META report they already separeted the Final Energy Consumption in the same nomenclature as the BEU
    """
EI_BEU = pd.read_csv("https://raw.githubusercontent.com/ottohebeda/Iron-and-steel-model/main/EI_Route_Step_year.csv")
EI_BEU =EI_BEU.fillna(0)

#dropping null values: Lenha, Produtos da cana, Gasolina, Querosene, Alcatrao, Alcool etilico

EI_BEU = EI_BEU[EI_BEU.Combustivel != 'Lenha']
EI_BEU = EI_BEU[EI_BEU.Combustivel != 'Produtos da cana']
EI_BEU = EI_BEU[EI_BEU.Combustivel != 'Gasolina']
EI_BEU = EI_BEU[EI_BEU.Combustivel != 'Querosene']
EI_BEU = EI_BEU[EI_BEU.Combustivel != 'Alcatrao']
EI_BEU = EI_BEU[EI_BEU.Combustivel != 'Alcool etilico']
EI_BEU = EI_BEU[EI_BEU.Combustivel != 'Outras fontes secundarias'] 

EI_BEU = EI_BEU.replace({'Combustivel':'Gases cidade'},'Gas cidade') #changing Gases cidade for Gas Cidade
EI_BEU = EI_BEU.replace({'Combustivel':'Outras fontes primarias'},'Outras fontes secundarias') #changing Outras primarias para outras secundarias

"""Importing Mitigation measures:"""

mitigation_measures = pd.read_csv("https://raw.githubusercontent.com/ottohebeda/Iron-and-steel-model/main/Iron_and_steel_mitigation_measures.csv")
mitigation_measures['Total Reduction GJ/t'] = mitigation_measures['Energy reduction (Gj/t)']*mitigation_measures.Penetration

#lifetime of mitigation measures:
life_time = 25 #years
mitigation_measures_dict = {}
for route in pd.unique(mitigation_measures.Route):
    mitigation_dict = {}
    mitigation = {}
    for etapa in pd.unique(mitigation_measures.loc[mitigation_measures['Route']==route,'Step']):
#        mitigation=mitigation_measures.loc[mitigation_measures['Route']==route].loc[mitigation_measures['Step']==etapa].set_index('Mitigation measure').drop(['Route','Step'],axis = 1).transpose().to_dict()
#        mitigation_dict[etapa] = mitigation
        mitigation=mitigation_measures.loc[mitigation_measures['Route']==route].set_index('Mitigation measure').drop(['Route'],axis = 1).transpose().to_dict()
    mitigation_measures_dict[route] = mitigation
    
# teste = mitigation_measures.loc[mitigation_measures['Route']==route].set_index('Mitigation measure').drop(['Route'],axis = 1).transpose().to_dict()

#Percentual of intensity reduction within each route and step
mitigation_measures['Percentual of reduction'] = 0
for indice in mitigation_measures.index:
    intensidade_Route_etapa= float(pd.DataFrame((mitigation_measures.loc[mitigation_measures['Route'] == mitigation_measures.loc[indice]['Route']].groupby('Step').sum()['Total Reduction GJ/t'])).loc[mitigation_measures.loc[indice]['Step']])
    if intensidade_Route_etapa == 0:
        pass
    else:
        mitigation_measures.loc[indice,'Percentual of reduction'] = mitigation_measures.loc[indice]['Total Reduction GJ/t']/intensidade_Route_etapa
        
innovation_measures = pd.read_csv('https://raw.githubusercontent.com/ottohebeda/Iron-and-steel-model/main/Innovation_measures.csv')

"""Importing Fuel prices"""
fuel_prices = pd.read_csv("https://raw.githubusercontent.com/ottohebeda/Iron-and-steel-model/main/fuel_price.csv")
fuel_prices['BRL/TJ'] = fuel_prices['BRL/ktep']/ktoe_to_tj 
fuel_prices = fuel_prices.set_index('Combustivel')
#fuel_prices.loc['Gas natural'] =fuel_prices.loc['Gas natural']/20
"""interest rate"""
interest_rate = 0.15
 
#%%
"""2. Historic Data"""

#Years from the historic data
past_years = np.linspace(2005,2020,2020-2005+1,dtype = int)

#Future years:
future_years = np.linspace(2021,2050,30,dtype = int)

#Base year (reference year for the projections)
base_year = 2020

#Energy Consumption in the Steel Production in the National Energy Balance (BEN)
 
Energy_consumption_BEN = pd.read_csv("https://raw.githubusercontent.com/ottohebeda/Industry_Energy_Emissions_simulator/main/CE_Siderurgia.csv") #importing BEN_Steel
Energy_consumption_BEN = Energy_consumption_BEN.fillna(0) #filling NA with 0
Energy_consumption_BEN = Energy_consumption_BEN.replace({'FONTES':'Carvao mineral'},'Carvao metalurgico') #changing Outras primarias para outras secundarias
Energy_consumption_BEN = Energy_consumption_BEN.replace({'FONTES':'Gas de coqueria'},'Gas cidade') #changing Outras primarias para outras secundarias
Energy_consumption_BEN = Energy_consumption_BEN.replace({'FONTES':'Alcatrao'},'Outras fontes secundarias') #changing Outras primarias para outras secundarias
Energy_consumption_BEN = Energy_consumption_BEN.set_index('FONTES') #Changin index for Sources
Energy_consumption_BEN.index = Energy_consumption_BEN.index.str.capitalize() #Change all UPPER to Capitalize
Energy_consumption_BEN.columns = Energy_consumption_BEN.columns.astype(int) #Changing the columns type: from str to int

#I'm going to drop Gás canalizado, Nafta and Querosene because they have value approximately zero:
#Energy_consumption_BEN = Energy_consumption_BEN.drop(index = ['Gás canalizado',"Nafta",'Querosene'])

#Slicing the Enerngy_consumption_BEN to values in the historical data:
#Energy_consumption_BEN =Energy_consumption_BEN.drop(columns = Energy_consumption_BEN.columns[0:35])

#Summing Biodeisel with Diesel to adjust the nomenclature:
Energy_consumption_BEN.loc['Oleo diesel'] = Energy_consumption_BEN.loc['Biodiesel']+Energy_consumption_BEN.loc['Oleo diesel']
Energy_consumption_BEN = Energy_consumption_BEN.drop(index = ['Biodiesel'])
Energy_consumption_BEN = Energy_consumption_BEN.rename(index = {'Glp': 'GLP'}) #fixing name
Energy_consumption_BEN = Energy_consumption_BEN .sort_index() #ordering the rows by fuel name
#Converting to Gj:
Energy_consumption_BEN_Gj = Energy_consumption_BEN*ktoe_to_tj 
#

#%%
"""Energy intensity of each route"""
R1_EI_Total = EI_BEU.loc[EI_BEU['Route'] == 'R1'].iloc[:,3:].sum()
R1_EI_Total.index = R1_EI_Total.index.astype(int)
R2_EI_Total = EI_BEU.loc[EI_BEU['Route'] == 'R2'].iloc[:,3:].sum()
R2_EI_Total.index = R2_EI_Total.index.astype(int)
R3_EI_Total = EI_BEU.loc[EI_BEU['Route'] == 'R3'].iloc[:,3:].sum()
R3_EI_Total.index = R3_EI_Total.index.astype(int)
R4_EI_Total = EI_BEU.loc[EI_BEU['Route'] == 'R4'].iloc[:,3:].sum()
R4_EI_Total.index = R4_EI_Total.index.astype(int)

#%%        
"""Energy Consumption"""

#R1 Energy Consumption:
R1_EC_Total = pd.DataFrame(index = R1_EI_Total.index, columns = ['Energy_Consumption'], data = 0)
for ano in past_years:
    R1_EC_Total.loc[ano] = R1_EI_Total.loc[ano]*steel_production['BOF MC'][ano]

#R2 Energy_consumption:
R2_EC_Total = pd.DataFrame(index = R1_EI_Total.index, columns = ['Energy_Consumption'], data = 0)
for ano in past_years:
    R2_EC_Total.loc[ano] = R2_EI_Total.loc[ano]*steel_production['BOF CC'][ano]

#R3_Energy_Cosumption:
R3_EC_Total = pd.DataFrame(index = R1_EI_Total.index, columns = ['Energy_Consumption'], data = 0)
for ano in past_years:
    R3_EC_Total.loc[ano] = R3_EI_Total.loc[ano]*steel_production['EAF'][ano]

#R4_Energy_Consumption:
R4_EC_Total = pd.DataFrame(index = R1_EI_Total.index, columns = ['Energy_Consumption'], data = 0)
for ano in past_years:
    R4_EC_Total.loc[ano] = R4_EI_Total.loc[ano]*pig_iron_production['Independente CV'][ano]    

"""Energy Consumption By Fuel"""
#This function calculates the energy consumption by fuel.
def energy_consumption(Route):
    """estimates the energy consumption using the Energy Intensity and the production"""
    
    EC_Total = pd.DataFrame(index = EI_BEU.index, columns = EI_BEU.columns, data = 0)
    EC_Total.Route = EI_BEU.Route
    EC_Total.Combustivel = EI_BEU.Combustivel
    EC_Total.Step = EI_BEU.Step
    
    #Energy consumption in R1:
    if Route =='R1':      
        for ano in EI_BEU.columns[3:]:
            for indice in EC_Total.loc[EC_Total['Route']=='R1'].index:
                EC_Total.loc[indice,str(ano)] = EI_BEU.loc[indice,str(ano)]*steel_production['BOF MC'][int(ano)] 
            
    #Energy consumption in R2
    if Route =='R2' :       
        for ano in EI_BEU.columns[3:]:
            for indice in EC_Total.loc[EC_Total['Route']=='R2'].index:
                EC_Total.loc[indice,str(ano)] = EI_BEU.loc[indice,str(ano)]*steel_production['BOF CC'][int(ano)]       
            
            #Energy consumption in R3   
    if Route == 'R3':
        for ano in EI_BEU.columns[3:]:
            for indice in EC_Total.loc[EC_Total['Route']=='R3'].index:
                EC_Total.loc[indice,str(ano)] = EI_BEU.loc[indice,str(ano)]*steel_production['EAF'][int(ano)]  
            
            #Energy consumption in R4
    if Route == 'R4':
        for ano in EI_BEU.columns[3:]:
            for indice in EC_Total.loc[EC_Total['Route']=='R4'].index:
                EC_Total.loc[indice,str(ano)] = EI_BEU.loc[indice,str(ano)]*pig_iron_production['Independente CV'][int(ano)]     
                
    if Route == 'todas':
        for ano in EI_BEU.columns[3:]:
            for indice in EC_Total.loc[EC_Total['Route']=='R1'].index:
                EC_Total.loc[indice,str(ano)] = EI_BEU.loc[indice,str(ano)]*steel_production['BOF MC'][int(ano)] 
        for ano in EI_BEU.columns[3:]:
            for indice in EC_Total.loc[EC_Total['Route']=='R2'].index:
                EC_Total.loc[indice,str(ano)] = EI_BEU.loc[indice,str(ano)]*steel_production['BOF CC'][int(ano)]                     
        for ano in EI_BEU.columns[3:]:
            for indice in EC_Total.loc[EC_Total['Route']=='R3'].index:
                EC_Total.loc[indice,str(ano)] = EI_BEU.loc[indice,str(ano)]*steel_production['EAF'][int(ano)]  
        for ano in EI_BEU.columns[3:]:
            for indice in EC_Total.loc[EC_Total['Route']=='R4'].index:
                EC_Total.loc[indice,str(ano)] = EI_BEU.loc[indice,str(ano)]*pig_iron_production['Independente CV'][int(ano)]     
                
    return EC_Total

#Energy consumption without calibration
Total_energy_consumption_R1 = energy_consumption('R1').groupby(['Combustivel'], axis =0, as_index = False).sum()
Total_energy_consumption_R2 = energy_consumption('R2').groupby(['Combustivel'], axis =0, as_index = False).sum()
Total_energy_consumption_R3 = energy_consumption('R3').groupby(['Combustivel'], axis =0, as_index = False).sum()
Total_energy_consumption_R4 = energy_consumption('R4').groupby(['Combustivel'], axis =0, as_index = False).sum()
Total_energy_consumption = energy_consumption('todas').groupby(['Combustivel'], axis =0, as_index = False).sum()

#%%
"""Adjustments for the energy consumption'"""

#Matching the Energy Intensity of each fuel, route and step to the energy consumption in the Energy Balance
for combustivel in Total_energy_consumption['Combustivel']:
    for ano in past_years:
        for i in EI_BEU.loc[EI_BEU['Combustivel'] == combustivel].index:
            EI_BEU[str(ano)][i] = EI_BEU[str(ano)][i]*Energy_consumption_BEN_Gj[ano][combustivel]/Total_energy_consumption.loc[Total_energy_consumption['Combustivel']==combustivel][str(ano)]

"""Creating dictionary"""

EI_dict= {}
a_dict = {}
for Route in pd.unique(EI_BEU['Route']):
    a_dict={}
    for etapa in pd.unique(EI_BEU.loc[EI_BEU['Route']==Route]['Step']):
        a =  EI_BEU.loc[EI_BEU['Route']==Route].loc[EI_BEU['Step']==etapa].set_index('Combustivel').drop(['Route','Step'],axis =1)
        a = a.to_dict()
        a_dict[etapa] = a
    EI_dict[Route] = a_dict   
#%%
"""Energy intensity of each route ajdusted """
R1_EI_Total = EI_BEU.loc[EI_BEU['Route'] == 'R1'].iloc[:,3:].sum()
R1_EI_Total.index = R1_EI_Total.index.astype(int)
R2_EI_Total = EI_BEU.loc[EI_BEU['Route'] == 'R2'].iloc[:,3:].sum()
R2_EI_Total.index = R2_EI_Total.index.astype(int)
R3_EI_Total = EI_BEU.loc[EI_BEU['Route'] == 'R3'].iloc[:,3:].sum()
R3_EI_Total.index = R3_EI_Total.index.astype(int)
R4_EI_Total = EI_BEU.loc[EI_BEU['Route'] == 'R4'].iloc[:,3:].sum()
R4_EI_Total.index = R4_EI_Total.index.astype(int)

"""Energy share by route"""

#Energy consumption after calibration;
Total_energy_consumption_R1 = energy_consumption('R1').groupby(['Combustivel'], axis =0, as_index = False).sum()
Total_energy_consumption_R2 = energy_consumption('R2').groupby(['Combustivel'], axis =0, as_index = False).sum()
Total_energy_consumption_R3 = energy_consumption('R3').groupby(['Combustivel'], axis =0, as_index = False).sum()
Total_energy_consumption_R4 = energy_consumption('R4').groupby(['Combustivel'], axis =0, as_index = False).sum()

#Creating Energy Share DataFrame by Route
Energy_share_R1 = Total_energy_consumption_R1.set_index('Combustivel')
Energy_share_R2 = Total_energy_consumption_R2.set_index('Combustivel')
Energy_share_R3 = Total_energy_consumption_R3.set_index('Combustivel')
Energy_share_R4 = Total_energy_consumption_R4.set_index('Combustivel')

Energy_share_R1.columns = Energy_share_R1.columns.astype(int)
Energy_share_R2.columns = Energy_share_R2.columns.astype(int)
Energy_share_R3.columns = Energy_share_R3.columns.astype(int)
Energy_share_R4.columns = Energy_share_R4.columns.astype(int)

#EnergyShare = Energy consumption/Total energy consumption
Energy_share_R1 = Energy_share_R1/Energy_share_R1.sum()
Energy_share_R2 = Energy_share_R2/Energy_share_R2.sum()
Energy_share_R3 = Energy_share_R3/Energy_share_R3.sum()
Energy_share_R4 = Energy_share_R4/Energy_share_R4.sum()

#Energy share will be conserved for future years:
for i in future_years:
    Energy_share_R1[i]=Energy_share_R1[base_year]
    Energy_share_R2[i]=Energy_share_R2[base_year]
    Energy_share_R3[i]=Energy_share_R3[base_year]
    Energy_share_R4[i]=Energy_share_R4[base_year]

#Energy Intensity for future years
for i in future_years:
    R1_EI_Total[i] = R1_EI_Total[base_year]
    R2_EI_Total[i] = R2_EI_Total[base_year]
    R3_EI_Total[i] = R3_EI_Total[base_year]
    R4_EI_Total[i] = R4_EI_Total[base_year]
    
#%%
"""Emission Base Reference"""
#Emission base reference is the amount of emissions when no measure is considered.
year = 2020
carbon_content = 0.01
def emission_calc (year):
    """This function estimates the emission in a given year. It uses the production in each route, the fuel share and the emission factor. After it removes the amount of carbon in the steel considering 1%"""
    emission = ((
        float(R1_EI_Total[year])*(float(steel_production.loc[year]['Share_BOF_MC']))*steel_production.loc[year]['Total']*sum(Energy_share_R1.loc[f][year]*emission_factor.loc[f]['CO2e'] for f in Energy_share_R1.index)
        +(float(R2_EI_Total[year]))*steel_production.loc[year]['Total']*(steel_production.loc[year]['Share_BOF_CC'])*sum(Energy_share_R2.loc[f][year]*emission_factor.loc[f]['CO2e'] for f in Energy_share_R2.index)
        +(float(R3_EI_Total[year]))*steel_production.loc[year]['EAF']*sum(Energy_share_R3.loc[f][year]*emission_factor.loc[f]['CO2e'] for f in Energy_share_R3.index)
        +(float(R4_EI_Total[year]))*pig_iron_production.loc[year]['Independente CV']*sum(Energy_share_R4.loc[f][year]*emission_factor.loc[f]['CO2e'] for f in Energy_share_R4.index)
        )/10**6
    -steel_production['Total'][year]*carbon_content*44/12/10**3)
    return emission

Emission_Reference = emission_calc (2020)
#%%
"""Steel production Projection"""

for year in np.linspace(2021,2050,2050-2021+1).astype(int):
    steel_production.loc[year] =np.full([len(steel_production.columns)],np.nan)
    pig_iron_production.loc[year] = np.full([len(pig_iron_production.columns)],np.nan)

Production_increase = {
        2030:1.2
        ,2040:1.5
        ,2050:1.7
        }

#Production route share will be equal to the values for the base year
steel_production.loc[2030][:5] = steel_production.loc[base_year][:5]*Production_increase[2030]
steel_production.loc[2040][:5] = steel_production.loc[base_year][:5]*Production_increase[2040]
steel_production.loc[2050][:5] = steel_production.loc[base_year][:5]*Production_increase[2050]
pig_iron_production.loc[2030][:3] = pig_iron_production.loc[base_year][:3]*Production_increase[2030]
pig_iron_production.loc[2040][:3] = pig_iron_production.loc[base_year][:3]*Production_increase[2040]
pig_iron_production.loc[2050][:3] = pig_iron_production.loc[base_year][:3]*Production_increase[2050]

steel_production['Share_BOF_MC'][2050] = steel_production['Share_BOF_MC'][base_year]
steel_production['Share_BOF_CC'][2050] = steel_production['Share_BOF_CC'][base_year]
steel_production['Share_EAF'][2050] = steel_production['Share_EAF'][base_year]
pig_iron_production['Share BOF CC'][2050] = pig_iron_production['Share BOF CC'][base_year]
pig_iron_production['Share BOF MC'][2050] = pig_iron_production['Share BOF MC'][base_year]

steel_production = steel_production.interpolate()
pig_iron_production= pig_iron_production.interpolate()

#%%
"""Optimization"""
#Creating model
def optimization_module(year,emission):
    
    """"For a givining Year and emission goal, the function will return mitigation measures, energy intensity, energy consumption, costs"""
    model = ConcreteModel()
         
    #Creating variables
    k1 = mitigation_measures_dict['R1'].keys() #list of the number of energy mitigation measures
    k2 = mitigation_measures_dict['R2'].keys()
    k3 = mitigation_measures_dict['R3'].keys()
    k4 =  mitigation_measures_dict['R4'].keys()
    
    model.X1 =  Var (k1,within =NonNegativeReals) #Energy efficiency mitigation measure in Route 1
    model.X2 =  Var (k2,within =NonNegativeReals) #Energy efficiency mitigation measure in Route 2
    model.X3 =  Var (k3,within =NonNegativeReals) #Energy efficiency mitigation measure in Route 3
    model.X4 =  Var (k4,within =NonNegativeReals) #Energy efficiency mitigation measure in Route 4
    model.X5= Var(within = NonNegativeReals) #DR-NG share 
    model.X6 = Var(within = NonNegativeReals) #Charcoal share
    model.X7 = Var(within = NonNegativeReals) #DR-H2 share
    model.X8 = Var(within= NonNegativeReals) #Smelting Reduction share
    model.X9 = Var(within = NonNegativeReals) #EAF
    #creating objective
    #minimize cost = (Capex+Opex)*Production*penetration
    ##Falta colocar a diferença de combustíveis.
    
    #Capex of each route
    capex_R1 = sum((mitigation_measures_dict['R1'][i]['CAPEX ($/t)'])*model.X1[i]*(float(steel_production.loc[year]['Share_BOF_MC'])-model.X5-model.X6-model.X7-model.X8-model.X9)*steel_production.loc[year]['Total']/1000 for i in k1)
    capex_R2 = sum((mitigation_measures_dict['R2'][i]['CAPEX ($/t)'])*model.X2[i]*steel_production.loc[year]['BOF CC']/1000 for i in k2)
    capex_R3 = sum((mitigation_measures_dict['R3'][i]['CAPEX ($/t)'])*model.X3[i]*steel_production.loc[year]['EAF']/1000 for i in k3)
    capex_R4 = sum((mitigation_measures_dict['R4'][i]['CAPEX ($/t)'])*model.X4[i]*pig_iron_production.loc[year]['Independente CV']/1000 for i in k4)
    capex_R5 = (model.X5*steel_production.loc[year]['Total']*innovation_measures.loc[0]['CAPEX (Euro/t)']/1000)
    capex_R6 = (model.X7*steel_production.loc[year]['Total']*innovation_measures.loc[2]['CAPEX (Euro/t)']/1000)
    capex_R7 = (model.X8*steel_production.loc[year]['Total']*innovation_measures.loc[4]['CAPEX (Euro/t)']/1000)
    
    opex_R1 = sum((mitigation_measures_dict['R1'][i]['OPEX ($/t)'])*model.X1[i]*(float(steel_production.loc[year]['Share_BOF_MC'])-model.X5-model.X6-model.X7-model.X8-model.X9)*steel_production.loc[year]['Total']/1000 for i in k1)
    opex_R2 = sum((mitigation_measures_dict['R2'][i]['OPEX ($/t)'])*model.X2[i]*steel_production.loc[year]['EAF']/1000 for i in k2)
    opex_R3 = sum((mitigation_measures_dict['R3'][i]['OPEX ($/t)'])*model.X3[i]*steel_production.loc[year]['BOF CC']/1000 for i in k3)
    opex_R4 = sum((mitigation_measures_dict['R4'][i]['OPEX ($/t)'])*model.X4[i]*pig_iron_production.loc[year]['Independente CV']/1000 for i in k4)
    opex_R5 = (model.X5*steel_production.loc[year]['Total']*innovation_measures.loc[0]['OPEX']/1000)
    opex_R6 = (model.X7*steel_production.loc[year]['Total']*innovation_measures.loc[2]['OPEX']/1000)
    opex_R7 = (model.X8*steel_production.loc[year]['Total']*innovation_measures.loc[4]['OPEX']/1000)
#    Emission mitigated considering energy efficiency measures and fuel shift
    Emission_mitigated_R1 = sum(model.X1[i]*mitigation_measures_dict['R1'][i]['Energy reduction (Gj/t)']*sum(EI_dict['R1'][mitigation_measures_dict['R1'][i]['Step']]['2020'][x]/sum(EI_dict['R1'][mitigation_measures_dict['R1'][i]['Step']]['2020'].values())*emission_factor.loc[x]['CO2e'] for x in EI_dict['R1'][mitigation_measures_dict['R1'][i]['Step']]['2020']) for i in k1)*(float(steel_production.loc[year]['Share_BOF_MC'])-model.X5-model.X6-model.X7-model.X8-model.X9)*steel_production.loc[year]['Total']/10**6
    Emission_mitigated_R2 = sum(model.X2[i]*mitigation_measures_dict['R2'][i]['Energy reduction (Gj/t)']*sum(EI_dict['R2'][mitigation_measures_dict['R2'][i]['Step']]['2020'][x]/sum(EI_dict['R2'][mitigation_measures_dict['R2'][i]['Step']]['2020'].values())*emission_factor.loc[x]['CO2e'] for x in EI_dict['R2'][mitigation_measures_dict['R2'][i]['Step']]['2020']) for i in k2)*steel_production.loc[year]['Total']*(model.X6 + steel_production.loc[year]['Share_BOF_CC'])/10**6
    Emission_mitigated_R3 = sum(model.X3[i]*mitigation_measures_dict['R3'][i]['Energy reduction (Gj/t)']*sum(EI_dict['R3'][mitigation_measures_dict['R3'][i]['Step']]['2020'][x]/sum(EI_dict['R3'][mitigation_measures_dict['R3'][i]['Step']]['2020'].values())*emission_factor.loc[x]['CO2e'] for x in EI_dict['R3'][mitigation_measures_dict['R3'][i]['Step']]['2020']) for i in k3)*steel_production.loc[year]['EAF']/10**6
    Emission_mitigated_R4 = sum(model.X4[i]*mitigation_measures_dict['R4'][i]['Energy reduction (Gj/t)']*sum(EI_dict['R4'][mitigation_measures_dict['R4'][i]['Step']]['2020'][x]/sum(EI_dict['R4'][mitigation_measures_dict['R4'][i]['Step']]['2020'].values())*emission_factor.loc[x]['CO2e'] for x in EI_dict['R4'][mitigation_measures_dict['R4'][i]['Step']]['2020']) for i in k4)*pig_iron_production.loc[year]['Independente CV']/10**6

#Energy consumption of new measures              
    EC_R5_calc = +model.X5*steel_production.loc[year]['Total']*innovation_measures.loc[0]['Energy_intensity (GJ/t)']
    EC_R6_calc = +model.X7*steel_production.loc[year]['Total']*innovation_measures.loc[2]['Energy_intensity (GJ/t)']
    EC_R7_calc = +model.X8*steel_production.loc[year]['Total']*innovation_measures.loc[4]['Energy_intensity (GJ/t)']
 
    #Energy consumption by route without energy efficiency measures:
    EC_R1_no_measure = (float(R1_EI_Total[year]))*(float(steel_production.loc[year]['Share_BOF_MC'])-model.X5-model.X6-model.X7-model.X8-model.X9)*steel_production.loc[year]['Total']
    EC_R2_no_measure=  (float(R2_EI_Total[year]))*steel_production.loc[year]['Total']*(model.X6+steel_production.loc[year]['Share_BOF_CC'])
    EC_R3_no_measure=+(float(R3_EI_Total[year]))*steel_production.loc[year]['Total']*(model.X9+steel_production.loc[year]['Share_EAF'])
    EC_R4_no_measure= +(float(R4_EI_Total[year]))*pig_iron_production.loc[year]['Independente CV']
    
    Emission_Baseline = (
            (EC_R1_no_measure*sum(Energy_share_R1.loc[f][year]*emission_factor.loc[f]['CO2e'] for f in Energy_share_R1.index)/10**6
            +EC_R2_no_measure * sum(Energy_share_R2.loc[f][year]*emission_factor.loc[f]['CO2e'] for f in Energy_share_R2.index)/10**6
            +EC_R3_no_measure *sum(Energy_share_R3.loc[f][year]*emission_factor.loc[f]['CO2e'] for f in Energy_share_R3.index)/10**6
            +EC_R4_no_measure*sum(Energy_share_R4.loc[f][year]*emission_factor.loc[f]['CO2e'] for f in Energy_share_R4.index)/10**6)
            
            )
    #Fuel cost when no measure is taken:
#    fuel_cost_no_measure =     (
#            EC_R1_no_measure*sum(Energy_share_R1.loc[f][year]*fuel_prices.loc[f]['BRL/TJ'] for f in Energy_share_R1.index)/10**6
#            +EC_R2_no_measure*sum(Energy_share_R2.loc[f][year]*fuel_prices.loc[f]['BRL/TJ'] for f in Energy_share_R2.index)/10**6
#            +EC_R3_no_measure*sum(Energy_share_R3.loc[f][year]*fuel_prices.loc[f]['BRL/TJ'] for f in Energy_share_R3.index)/10**6
#            +EC_R4_no_measure*sum(Energy_share_R4.loc[f][year]*fuel_prices.loc[f]['BRL/TJ'] for f in Energy_share_R4.index)/10**6            
#            )
##    Fuel cost when applying mitigation measures: REFAZER
    #Acho que posso estar esquecendo de colocar o acréscimo do custo de combustíveis ao usar carvão vegetal
    #Energy saving = Penetration of a given technology * Reduction in GJ/t  * (energy share * fuel price) * production
    Energy_saving_R1 = sum(model.X1[i]*mitigation_measures_dict['R1'][i]['Energy reduction (Gj/t)']*sum(EI_dict['R1'][mitigation_measures_dict['R1'][i]['Step']]['2020'][x]/sum(EI_dict['R1'][mitigation_measures_dict['R1'][i]['Step']]['2020'].values())*fuel_prices.loc[x]['BRL/TJ'] for x in EI_dict['R1'][mitigation_measures_dict['R1'][i]['Step']]['2020']) for i in k1)*(float(steel_production.loc[year]['Share_BOF_MC'])-model.X5-model.X6-model.X7-model.X8-model.X9)*steel_production.loc[year]['Total']/10**6
    Energy_saving_R2 = sum(model.X2[i]*mitigation_measures_dict['R2'][i]['Energy reduction (Gj/t)']*sum(EI_dict['R2'][mitigation_measures_dict['R2'][i]['Step']]['2020'][x]/sum(EI_dict['R2'][mitigation_measures_dict['R2'][i]['Step']]['2020'].values())*fuel_prices.loc[x]['BRL/TJ'] for x in EI_dict['R2'][mitigation_measures_dict['R2'][i]['Step']]['2020']) for i in k2)*steel_production.loc[year]['Total']*(model.X6 + steel_production.loc[year]['Share_BOF_CC'])/10**6
    Energy_saving_R3 = sum(model.X3[i]*mitigation_measures_dict['R3'][i]['Energy reduction (Gj/t)']*sum(EI_dict['R3'][mitigation_measures_dict['R3'][i]['Step']]['2020'][x]/sum(EI_dict['R3'][mitigation_measures_dict['R3'][i]['Step']]['2020'].values())*fuel_prices.loc[x]['BRL/TJ'] for x in EI_dict['R3'][mitigation_measures_dict['R3'][i]['Step']]['2020']) for i in k3)*steel_production.loc[year]['Total']*(model.X9+steel_production.loc[year]['Share_EAF'])/10**6
    Energy_saving_R4 = sum(model.X4[i]*mitigation_measures_dict['R4'][i]['Energy reduction (Gj/t)']*sum(EI_dict['R4'][mitigation_measures_dict['R4'][i]['Step']]['2020'][x]/sum(EI_dict['R4'][mitigation_measures_dict['R4'][i]['Step']]['2020'].values())*fuel_prices.loc[x]['BRL/TJ'] for x in EI_dict['R4'][mitigation_measures_dict['R4'][i]['Step']]['2020']) for i in k4)*pig_iron_production.loc[year]['Independente CV']/10**6

    Energy_cost_R5_R7 = +(model.X5*steel_production.loc[year]['Total']*innovation_measures.loc[0]['Energy_intensity (GJ/t)'] + model.X7*steel_production.loc[year]['Total']*innovation_measures.loc[2]['Energy_intensity (GJ/t)'])*fuel_prices.loc['Gas natural']['BRL/TJ']/10**6
    +(model.X8*steel_production.loc[year]['Total']*innovation_measures.loc[4]['Energy_intensity (GJ/t)'])*fuel_prices.loc['Carvao vegetal']['BRL/TJ']/10**6
    +(model.X5*steel_production.loc[year]['Total']*innovation_measures.loc[1]['Energy_intensity (GJ/t)'] + model.X7*steel_production.loc[year]['Total']*innovation_measures.loc[3]['Energy_intensity (GJ/t)']+model.X8*steel_production.loc[year]['Total']*innovation_measures.loc[5]['Energy_intensity (GJ/t)'])*fuel_prices.loc['Eletricidade']['BRL/TJ']/10**6
   
  
#    Fuel economy: Fuel cost A - Fuel cost saving
    fuel_saving = Energy_saving_R1+ Energy_saving_R2 + Energy_saving_R3+ Energy_saving_R4 - Energy_cost_R5_R7

    carbon_price = 10 #dollars per ton
#    carbon_cost= 
    
    model.obj= Objective(expr =(capex_R1+ capex_R2+capex_R3 + capex_R4 + capex_R5  + model.X6*1+ capex_R6+capex_R7)*interest_rate*((1+interest_rate)**20)/((1+interest_rate)**20-1)
                         +opex_R1+opex_R2+opex_R3+opex_R4+opex_R5+opex_R6+opex_R7
                         -fuel_saving/5 #Falta arrumar o custo do vegetal e o custo em dolar
    )
    
    #Restrictions
    model.con = ConstraintList()
    
    ##Penetration
    for i in k1:
        model.con.add(model.X1[i] <= float(mitigation_measures_dict['R1'][i]['Penetration']))
    for i in k2:
        model.con.add (model.X2[i]<=float(mitigation_measures_dict['R2'][i]['Penetration']))
    for i in k3:
        model.con.add (model.X3[i]<=float(mitigation_measures_dict['R3'][i]['Penetration']))
    for i in k4:
        model.con.add (model.X4[i]<=float(mitigation_measures_dict['R4'][i]['Penetration']))
        
    model.con.add(model.X5<=innovation_measures.loc[0]['Penetration']) #Ajustar para não ficar o índice numérico
    model.con.add(model.X6<=0.1) #charcoal limite
    model.con.add(model.X7<=innovation_measures.loc[2]['Penetration']) #Ajustar
    model.con.add(model.X8<=0.1)
    model.con.add(model.X9<=0.14)
    model.con.add(model.X5+model.X6+model.X7+model.X8 +model.X9 <= float(steel_production.loc[year]['Share_BOF_MC']))
    
    
    ##Emissions:
        ##Emissions = Intensity_Route(1-Mitigation)*Energy_Share_Route*Production_Route*emission_factor         

#exemplo de como posso fazer o calculo das emissoes
    def emission_calc_route (route):
        emission = 0
        for step in EI_dict[route].keys():
            emission = emission+sum(EI_dict[route][step]['2020'][f]*emission_factor.loc[f]['CO2e'] for f in EI_dict[route][step]['2020'].keys())
        return emission
    
    Emission_R1 = emission_calc_route('R1')
    Emission_R2 =emission_calc_route('R2')
    Emission_R3 =emission_calc_route('R3')
    Emission_R4 =emission_calc_route('R4')
#Emission_R1 = sum(EI_dict['R1']['Alto-forno']['2020'][f]*emission_factor.loc[f]['CO2e'] for f in EI_dict['R1']['Alto-forno']['2020'].keys())

#Tem que colocar o 5 e o 6 como redução das emissões.
    model.con.add(
            Emission_Baseline
            -(Emission_mitigated_R1
            +Emission_mitigated_R2
           + Emission_mitigated_R3
            +Emission_mitigated_R4)
            +EC_R5_calc*emission_factor.loc['Gas natural']['CO2e']/10**6
            +EC_R6_calc*emission_factor.loc['Gas natural']['CO2e']/10**6
            +EC_R7_calc*emission_factor.loc['Carvao vegetal']['CO2e']/10**6
            -steel_production['Total'][year]*carbon_content*44/12/10**3
            ==emission
            )
    
    # Solving the problem:
    solver = SolverFactory('ipopt')
    result_solver = solver.solve(model, tee = True)
    
#    CE = (
#            EC_R1_calc()*Energy_share_R1[year]
##            +EC_R2_calc()*Energy_share_R2[year]
##            +EC_R3_calc()*Energy_share_R3[year]
##            +EC_R4_calc()*Energy_share_R4[year]
#            )
    
    #Summing the energy consumption from innovative measures:
#    CE['Gas natural'] = CE['Gas natural']+model.X5()*steel_production.loc[year]['Total']*innovation_measures.loc[0]['Energy_intensity (GJ/t)']*10**3 + model.X7()*steel_production.loc[year]['Total']*innovation_measures.loc[2]['Energy_intensity (GJ/t)']*10**3
#    CE['Eletricidade'] = CE['Eletricidade']+model.X5()*steel_production.loc[year]['Total']*innovation_measures.loc[1]['Energy_intensity (GJ/t)']*10**3 + model.X7()*steel_production.loc[year]['Total']*innovation_measures.loc[3]['Energy_intensity (GJ/t)']*10**3
     
    return model
#%%
"""Future emissions, costs and energy consumption"""

Emission_reduction = {
        2025:0.9,
        2030:0.80,
        2035:0.7,
        2040:.6,
        2045:0.5,
        2050:0.4
                      } 

Emission_base = {
        2025:1,
        2030:1,
        2035:1,
        2040:1,
        2045:1,
        2050:1
                      } 

Results = pd.DataFrame(columns = [2025,2030,2035,2040,2045,2050],index = ['Cost','Emissions','Energy Consumption','Fuel_saving','GN','CV','H2','SR','EAF','EmissionR1'],data= 0,dtype=float)
X1 = pd.DataFrame(columns = [2025,2030,2035,2040,2045,2050], index =  mitigation_measures_dict['R1'].keys(),data= 0,dtype=float)

for i in Emission_reduction:
    x= optimization_module(i,emission_calc(i)*Emission_reduction[i])
    Results[i]['Cost'] = float(x.obj())
    Results[i]['Emissions'] = emission_calc(i)*Emission_reduction[i]
    Results.loc['GN'][i]= float(x.X5())
    Results.loc['CV'][i]= x.X6()+steel_production['Share_BOF_CC'][i]
    Results.loc['H2'][i]= x.X7()
    Results.loc['SR'][i]=x.X8()
    Results.loc['EAF'][i]=x.X9() +steel_production['Share_EAF'][i]
    X1[i] =x.X1[:]()
#    Results[i]['Energy Consumption'] = y.sum()
#    Results[i]['Fuel_saving'] = fuel_saving()

#%% 
    
"""Creating a Cost Curve for the Steel industry"""
#
cost_curve = pd.DataFrame(columns = ['Cost'],index = np.linspace(0.99,0.40,20),data = 0, dtype=float)
emission_mitigated = pd.DataFrame(columns = ['Emission mitigated'], index = np.linspace(0.99,0.40,20), data = 0, dtype = float)

for i in np.linspace(0.99,0.4,20):
    x= optimization_module(2020,emission_calc(2020)*i)
    emission_mitigated.loc[i] = emission_calc(2020)-emission_calc(2020)*i
    cost_curve.loc[i] = float(x.obj())/float(emission_mitigated.loc[i])

plt.plot(emission_mitigated, cost_curve)
    

#for step in EI_dict['R1'].keys():
#    for measure in mitigation_measures_dict['R1']:
#        if  step == mitigation_measures_dict['R1'][measure]['Step']:
#            print(measure,mitigation_measures_dict['R1'][measure]['Step'],step == mitigation_measures_dict['R1'][measure]['Step'])
#        else:
#            pass
#        
#for i in k1:
#    for x in EI_dict['R1'][mitigation_measures_dict['R1'][i]['Step']]['2020']:
#        EI_dict['R1'][mitigation_measures_dict['R1'][i]['Step']]['2020'][x] *=1-model.X1()*mitigation_measures_dict['R1'][i]['Energy reduction (Gj/t)']
        
        