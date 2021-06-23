# -*- coding: utf-8 -*-
"""
Created on Sun Dec 20 12:12:10 2020

@author: Otto

Energy and Emission Bottom-up modelling: Iron and Steel V2

V2 - Dictionary instead Pandas for the Energy Intensity by route

R1 = Route BOF using Coal
R2 = Route BOF using Charcoal
R3 = Route EAF using scrap
R4 = Route Independet producers 
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#%%
"""1. Importing Data"""

#Confersion factor Gj to Ktoe    
gj_to_ktoe = 1/41.868
ktoe_to_gj = 41.868

#Greenhouse gases Global Warning Potential GWP:
GWP = {'CH4':28,'N2O':265}

"""Importing Crude Steel production by route"""

steel_production = pd.read_csv("https://raw.githubusercontent.com/ottohebeda/Iron-and-steel-model/main/steel_production.csv")
steel_production = steel_production.set_index('Year')
steel_production['Total']= steel_production.sum(axis=1)

"""Importing Pig Iron production by Route"""
pig_iron_production = pd.read_csv("https://raw.githubusercontent.com/ottohebeda/Iron-and-steel-model/main/Pig_iron_production.csv")
pig_iron_production = pig_iron_production.set_index('Ano')
pig_iron_production['Share BOF CC'] = pig_iron_production['Integrada CV']/(pig_iron_production['Integrada CV']+pig_iron_production['Integrada CM'])
pig_iron_production['Share BOF MC']=1-pig_iron_production['Share BOF CC']

"""Importing Emission Factor"""
emission_factor = pd.read_csv("https://raw.githubusercontent.com/ottohebeda/Iron-and-steel-model/main/emission_factor.csv")

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
mitigation_measures['Total Reduction GJ/t'] = mitigation_measures['Reducao na intensidade (Gj/t)']*mitigation_measures.Penetracao
#Percentual of intensity reduction within each route and step

mitigation_measures['Percentual of reduction'] = 0
for indice in mitigation_measures.index:
    intensidade_rota_etapa= float(pd.DataFrame((mitigation_measures.loc[mitigation_measures['Rota'] == mitigation_measures.loc[indice]['Rota']].groupby('Etapa').sum()['Total Reduction GJ/t'])).loc[mitigation_measures.loc[indice]['Etapa']])
    if intensidade_rota_etapa == 0:
        pass
    else:
        mitigation_measures.loc[indice,'Percentual of reduction'] = mitigation_measures.loc[indice]['Total Reduction GJ/t']/intensidade_rota_etapa

"""Importing Fuel prices"""
fuel_prices = pd.read_csv("https://raw.githubusercontent.com/ottohebeda/Iron-and-steel-model/main/fuel_price.csv")
fuel_prices['BRL/GJ'] = fuel_prices['BRL/ktep']/ktoe_to_gj

#%%
"""2. Historic Data"""

#Years from the historic data
past_years = np.linspace(2005,2019,2019-2005+1)
past_years = past_years.astype(int)

#Energy Consumption in the Steel Production in the National Energy Balance (BEN)
 
Energy_consumption_BEN = pd.read_csv("https://raw.githubusercontent.com/ottohebeda/Iron-and-steel-model/main/BEN_IronSteel_2019.csv") #importing BEN_Steel
Energy_consumption_BEN = Energy_consumption_BEN.fillna(0) #filling NA with 0
Energy_consumption_BEN = Energy_consumption_BEN.set_index('SOURCES') #Changin index for Sources
Energy_consumption_BEN.index = Energy_consumption_BEN.index.str.capitalize() #Change all UPPER to Capitalize
Energy_consumption_BEN.columns = Energy_consumption_BEN.columns.astype(int) #Changing the columns type: from str to int

#I'm going to drop Gás canalizado, Nafta and Querosene because they have value approximately zero:
Energy_consumption_BEN = Energy_consumption_BEN.drop(index = ['Gás canalizado',"Nafta",'Querosene'])

#Slicing the Enerngy_consumption_BEN to values in the historical data:
Energy_consumption_BEN =Energy_consumption_BEN.drop(columns = Energy_consumption_BEN.columns[0:35])


#Summing Biodeisel with Diesel to adjust the nomenclature:
Energy_consumption_BEN.loc['Oleo diesel'] = Energy_consumption_BEN.loc['Biodiesel']+Energy_consumption_BEN.loc['Oleo diesel']
Energy_consumption_BEN = Energy_consumption_BEN.drop(index = ['Biodiesel'])
Energy_consumption_BEN = Energy_consumption_BEN.rename(index = {'Glp': 'GLP'}) #fixing name
Energy_consumption_BEN = Energy_consumption_BEN .sort_index() #ordering the rows by fuel name
#Converting to Gj:
Energy_consumption_BEN_Gj = Energy_consumption_BEN*ktoe_to_gj 
#

#%%
"""Energy intensity of each route"""
R1_EI_Total = EI_BEU.loc[EI_BEU['Rota'] == 'R1'].iloc[:,3:].sum()
R2_EI_Total = EI_BEU.loc[EI_BEU['Rota'] == 'R2'].iloc[:,3:].sum()
R3_EI_Total = EI_BEU.loc[EI_BEU['Rota'] == 'R3'].iloc[:,3:].sum()
R4_EI_Total = EI_BEU.loc[EI_BEU['Rota'] == 'R4'].iloc[:,3:].sum()


#%%        
"""Energy Consumption"""

#BOF Coal production in Mt
steel_production['BOF MC'] = steel_production.BOF*pig_iron_production['Share BOF MC']

#BOF Charcoal production in Mt
steel_production['BOF CC'] = steel_production.BOF*pig_iron_production['Share BOF CC']

#R1 Energy Consumption:
R1_EC_Total = pd.DataFrame(index = R1_EI_Total.index, columns = ['Energy_Consumption'], data = 0)
for ano in past_years:
    R1_EC_Total.loc[str(ano)] = R1_EI_Total.loc[str(ano)]*steel_production['BOF MC'][ano]

#R2 Energy_consumption:
R2_EC_Total = pd.DataFrame(index = R1_EI_Total.index, columns = ['Energy_Consumption'], data = 0)
for ano in past_years:
    R2_EC_Total.loc[str(ano)] = R2_EI_Total.loc[str(ano)]*steel_production['BOF CC'][ano]

#R3_Energy_Cosumption:
R3_EC_Total = pd.DataFrame(index = R1_EI_Total.index, columns = ['Energy_Consumption'], data = 0)
for ano in past_years:
    R3_EC_Total.loc[str(ano)] = R3_EI_Total.loc[str(ano)]*steel_production['EAF'][ano]

#R4_Energy_Consumption:
R4_EC_Total = pd.DataFrame(index = R1_EI_Total.index, columns = ['Energy_Consumption'], data = 0)
for ano in past_years:
    R4_EC_Total.loc[str(ano)] = R4_EI_Total.loc[str(ano)]*pig_iron_production['Independente CV'][ano]    

"""Energy Consumption By Fuel"""
#This function calculates the energy consumption by fuel.
def energy_consumption(Rota):
    """estimates the energy consumption using the Energy Intensity and the production"""
    
    EC_Total = pd.DataFrame(index = EI_BEU.index, columns = EI_BEU.columns, data = 0)
    EC_Total.Rota = EI_BEU.Rota
    EC_Total.Combustivel = EI_BEU.Combustivel
    EC_Total.Etapa = EI_BEU.Etapa
    
    #Energy consumption in R1:
    if Rota =='R1' or 'todas':      
        for ano in EI_BEU.columns[3:]:
            for indice in EC_Total.loc[EC_Total['Rota']=='R1'].index:
                EC_Total.loc[indice,str(ano)] = EI_BEU.loc[indice,str(ano)]*steel_production['BOF MC'][int(ano)] 
            
    #Energy consumption in R2
    if Rota =='R2' or 'todas':       
        for ano in EI_BEU.columns[3:]:
            for indice in EC_Total.loc[EC_Total['Rota']=='R2'].index:
                EC_Total.loc[indice,str(ano)] = EI_BEU.loc[indice,str(ano)]*steel_production['BOF CC'][int(ano)]       
            
            #Energy consumption in R3   
    if Rota == 'R3' or 'todas':
        for ano in EI_BEU.columns[3:]:
            for indice in EC_Total.loc[EC_Total['Rota']=='R3'].index:
                EC_Total.loc[indice,str(ano)] = EI_BEU.loc[indice,str(ano)]*steel_production['EAF'][int(ano)]  
            
            #Energy consumption in R4
    if Rota == 'R4' or 'todas':
        for ano in EI_BEU.columns[3:]:
            for indice in EC_Total.loc[EC_Total['Rota']=='R4'].index:
                EC_Total.loc[indice,str(ano)] = EI_BEU.loc[indice,str(ano)]*pig_iron_production['Independente CV'][int(ano)]       

    return EC_Total

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
     
#%%
"""Energy intensity of each route ajdusted """
R1_EI_Total = EI_BEU.loc[EI_BEU['Rota'] == 'R1'].iloc[:,3:].sum()
R2_EI_Total = EI_BEU.loc[EI_BEU['Rota'] == 'R2'].iloc[:,3:].sum()
R3_EI_Total = EI_BEU.loc[EI_BEU['Rota'] == 'R3'].iloc[:,3:].sum()
R4_EI_Total = EI_BEU.loc[EI_BEU['Rota'] == 'R4'].iloc[:,3:].sum()

#%%
"""Energy Consumption after adjustments"""

"""Energy Consumption"""

#BOF Coal production in Mt
steel_production['BOF MC'] = steel_production.BOF*pig_iron_production['Share BOF MC']

#BOF Charcoal production in Mt
steel_production['BOF CC'] = steel_production.BOF*pig_iron_production['Share BOF CC']

#####ACHO QUE POSSO TIRAR ISSO AQUI::::
#R1 Energy Consumption:
R1_EC_Total = pd.DataFrame(index = R1_EI_Total.index, columns = ['Energy_Consumption'], data = 0)
for ano in past_years:
    R1_EC_Total.loc[str(ano)] = R1_EI_Total.loc[str(ano)]*steel_production['BOF MC'][ano]

#R2 Energy_consumption:
R2_EC_Total = pd.DataFrame(index = R1_EI_Total.index, columns = ['Energy_Consumption'], data = 0)
for ano in past_years:
    R2_EC_Total.loc[str(ano)] = R2_EI_Total.loc[str(ano)]*steel_production['BOF CC'][ano]

#R3_Energy_Cosumption:
R3_EC_Total = pd.DataFrame(index = R1_EI_Total.index, columns = ['Energy_Consumption'], data = 0)
for ano in past_years:
    R3_EC_Total.loc[str(ano)] = R3_EI_Total.loc[str(ano)]*steel_production['EAF'][ano]

#R4_Energy_Consumption:
R4_EC_Total = pd.DataFrame(index = R1_EI_Total.index, columns = ['Energy_Consumption'], data = 0)
for ano in past_years:
    R4_EC_Total.loc[str(ano)] = R4_EI_Total.loc[str(ano)]*pig_iron_production['Independente CV'][ano]    
######################
    
"""Energy Consumption By Fuel"""
Total_energy_consumption_2 = energy_consumption('todas').groupby(['Combustivel'], axis =0, as_index = False).sum()

#%%

"""Projecting the production of Iron and Steel"""

activity_increase_2019 = {2030:1.7,2050:2} #Increase of the production of steel in comparison to 2019
projected_years = np.linspace(2020,2050,2050-2020+1)
projected_years = projected_years.astype(int)

#Creating columns for the share of the routes BOF and EAF production:
steel_production['Total+EOF'] = steel_production['Total'] #Removing EOF production
steel_production['Total'] = steel_production['Total'] - steel_production['EOF']

#Share of each route:
steel_production['Share BOF'] = steel_production['BOF']/steel_production['Total']
steel_production['Share BOF CC'] = steel_production['BOF CC']/steel_production['Total']
steel_production['Share BOF MC'] = steel_production['BOF MC']/steel_production['Total']
steel_production['Share EAF'] = steel_production['EAF']/steel_production['Total']

#Creating the projected years:
for year in np.linspace(2020,2050,2050-2020+1):
    steel_production.loc[year] = np.nan
    pig_iron_production.loc[year] = np.nan

#projecting the share of BOF CC, BOF MC and EAF in a BAU scenario:
steel_production['Share BOF CC'][2030] = steel_production['Share BOF CC'][2019]*1
steel_production['Share BOF CC'][2040] = steel_production['Share BOF CC'][2019]*1
steel_production['Share BOF CC'][2050] = steel_production['Share BOF CC'][2019]*1
steel_production['Share BOF CC'] = steel_production['Share BOF CC'].interpolate()

steel_production['Share EAF'][2030] = steel_production['Share EAF'][2019] *1
steel_production['Share EAF'][2040] = steel_production['Share EAF'][2019] *1
steel_production['Share EAF'][2050] = steel_production['Share EAF'][2019] *1
steel_production['Share EAF'] = steel_production['Share EAF'].interpolate()

steel_production['Share BOF MC'] = 1-steel_production['Share EAF']-steel_production['Share BOF CC']
steel_production['Share BOF'] = 1-steel_production['Share EAF']
    
#The independent production of pig iron follows the growth of the steel production
for ano in activity_increase_2019.keys():
    pig_iron_production['Independente CV'][ano] = pig_iron_production['Independente CV'][2019]*activity_increase_2019[ano]
pig_iron_production['Independente CV'] = pig_iron_production['Independente CV'].interpolate()

#Projection of the Total production of Steel:
for ano in activity_increase_2019.keys():
    steel_production['Total'][ano]= steel_production['Total'][2019]*activity_increase_2019[ano]

steel_production['Total']= steel_production['Total'].interpolate()

#estimating BOF  and EAF production (Mt):
steel_production['EAF'] = steel_production['Total']*steel_production['Share EAF']
steel_production['BOF MC'] = steel_production['Total']*steel_production['Share BOF MC']
steel_production['BOF CC'] = steel_production['Total']*steel_production['Share BOF CC']
steel_production['BOF'] = steel_production['BOF CC']+steel_production['BOF MC']

#%%
"""Estimating the projected Energy Consumption"""

#Primeiro projetar a intensidade energética
for year in projected_years:
    EI_BEU[str(year)]= EI_BEU['2019']

#depois vou fazer a operação de multipliar a intesnidade energética pela produção
Energy_consumption_projected = energy_consumption('todas')
Total_energy_consumption_projected = energy_consumption('todas').groupby(['Combustivel'], axis =0, as_index = False).sum()
Total_energy_consumption_projected.loc[10] = Total_energy_consumption_projected.sum()
Total_energy_consumption_projected = Total_energy_consumption_projected.replace(Total_energy_consumption_projected.loc[10]['Combustivel'], 'Total')

#%%
"""Calculation of the emissions of GHG"""

#Process emissions (source: MCTIC,2015 - Terceiro inventario: produção de metais)

#Process fuels and Energy Fuels
process_fuels = ['Carvao metalurgico', 'Coque de carvao mineral','Carvao vegetal']

energy_fuels = list(Energy_consumption_BEN.index)
energy_fuels.remove('Total') #excluding total
energy_fuels.remove('Eletricidade') #excluding Eletricity because its has not emission intensity
for fuel in process_fuels: #removing the Process fuels
    energy_fuels.remove(fuel)


def emission_process_calc (Total_energy,production,GHG,fuel_set):
    """Function for calculating the emission in iron and steel process. Return the emissions in Gg"""
    if GHG == 'CO2':
        for combustivel in fuel_set:
            if combustivel == fuel_set[0]:
                emissions = (Total_energy.loc[Total_energy['Combustivel']==combustivel,'2005':]*float(emission_factor.loc[emission_factor['Combustivel']==combustivel,GHG])/1000)
            elif combustivel== 'Carvao vegetal':
                pass
            else:
                emissions = emissions.append (Total_energy.loc[Total_energy['Combustivel']==combustivel,'2005':]*float(emission_factor.loc[emission_factor['Combustivel']==combustivel,GHG])/1000)
        if production.any() == pig_iron_production['Independente CV'].any():
            return emissions
        else:
            return emissions-emissions/emissions.sum()*np.array(production*0.01)
    else:
        for combustivel in fuel_set:
            if combustivel == fuel_set[0]:
                emissions = (Total_energy.loc[Total_energy['Combustivel']==combustivel,'2005':]*float(emission_factor.loc[emission_factor['Combustivel']==combustivel,GHG])/1000)
            else:
                emissions = emissions.append (Total_energy.loc[Total_energy['Combustivel']==combustivel,'2005':]*float(emission_factor.loc[emission_factor['Combustivel']==combustivel,GHG]))/1000  
        return emissions
                                          

#Process CO2 emissions:
Process_CO2_emissions = emission_process_calc(Total_energy_consumption_projected,steel_production['Total'],'CO2',process_fuels).sum() 

#Process_CH4_emissions:
Process_CH4_emissions = emission_process_calc(Total_energy_consumption_projected,steel_production['Total'],'CH4',process_fuels).sum()

#Process_N2O_emissions
Process_N2O_emissions = emission_process_calc(Total_energy_consumption_projected,steel_production['Total'],'N2O',process_fuels).sum()

#Energy Emissions:
def emission_energy_calc(Total_energy,GHG,fuel_set):
    """This functions calculates the emissions from energy in Iron and steel. Return the emissions in Gg"""
    if GHG == 'CO2':
        for combustivel in fuel_set:
            if combustivel == fuel_set[0]:
                emissions = (Total_energy.loc[Total_energy['Combustivel']==combustivel,'2005':]*float(emission_factor.loc[emission_factor['Combustivel']==combustivel,GHG])/1000)
            elif combustivel== 'Carvao vegetal':
                pass
            else:
                emissions = emissions.append (Total_energy.loc[Total_energy['Combustivel']==combustivel,'2005':]*float(emission_factor.loc[emission_factor['Combustivel']==combustivel,GHG])/1000)
        return emissions
    else:
        for combustivel in fuel_set:
            if combustivel == fuel_set[0]:
                emissions = (Total_energy.loc[Total_energy['Combustivel']==combustivel,'2005':]*float(emission_factor.loc[emission_factor['Combustivel']==combustivel,GHG])/1000)
            else:
                emissions = emissions.append (Total_energy.loc[Total_energy['Combustivel']==combustivel,'2005':]*float(emission_factor.loc[emission_factor['Combustivel']==combustivel,GHG])/1000)
        return emissions
    

#Energy CO2 emissions:
Energy_CO2_emissions = emission_energy_calc(Total_energy_consumption_projected,'CO2',energy_fuels)

#Energy CH4 emissions:
Energy_CH4_emissions = emission_energy_calc(Total_energy_consumption_projected,'CH4',energy_fuels) 

#Energy N2O emissions:
Energy_N2O_emissions = emission_energy_calc(Total_energy_consumption_projected,'N2O',energy_fuels)

#Total emissions:
Emissions_projected_CO2 = Process_CO2_emissions + Energy_CO2_emissions.sum()
Emissions_projected_CH4 = Process_CH4_emissions + Energy_CH4_emissions.sum()
Emissions_projected_N2O = Process_N2O_emissions + Energy_N2O_emissions.sum()



#%%
"Mitigation Measures"""

#-------
"""Changing the share of production"""
#------------------------------------------------------------------------------------------------------------
"""a. Incrasing Charcoal production"""

charcoal_increase = {2030:1.1,2040:1.2,2050:1.3} #How much the share of charcoal will increase in comparison to 2019
EAF_increase = {2030:1.1,2040:1.2,2050:1.3} #How much the share of EAF will increase in comparison to 2019

for year in np.linspace(2020,2050,2050-2020+1):
    steel_production.loc[year,] = np.nan
    pig_iron_production.loc[year,] = np.nan
    
steel_production['Share BOF CC'][2030] = steel_production['Share BOF CC'][2019]*charcoal_increase[2030]
steel_production['Share BOF CC'][2040] = steel_production['Share BOF CC'][2019]*charcoal_increase[2040]
steel_production['Share BOF CC'][2050] = steel_production['Share BOF CC'][2019]*charcoal_increase[2050]
steel_production['Share BOF CC'] = steel_production['Share BOF CC'].interpolate()

steel_production['Share EAF'][2030] = steel_production['Share EAF'][2019] 
steel_production['Share EAF'][2040] = steel_production['Share EAF'][2019] 
steel_production['Share EAF'][2050] = steel_production['Share EAF'][2019] 
steel_production['Share EAF'] = steel_production['Share EAF'].interpolate()

steel_production['Share BOF MC'] = 1-steel_production['Share EAF']-steel_production['Share BOF CC']
steel_production['Share BOF'] = 1-steel_production['Share EAF']
  
#The independent production of pig iron follows the growth of the steel production
for ano in activity_increase_2019.keys():
    pig_iron_production['Independente CV'][ano] = pig_iron_production['Independente CV'][2019]*activity_increase_2019[ano]

pig_iron_production['Independente CV'] = pig_iron_production['Independente CV'].interpolate()

#Projection of the Total production of Steel:
for ano in activity_increase_2019.keys():
    steel_production['Total'][ano]= steel_production['Total'][2019]*activity_increase_2019[ano]
    
steel_production['Total']= steel_production['Total'].interpolate()

#estimating BOF  and EAF production (Mt):
steel_production['EAF'] = steel_production['Total']*steel_production['Share EAF']
steel_production['BOF MC'] = steel_production['Total']*steel_production['Share BOF MC']
steel_production['BOF CC'] = steel_production['Total']*steel_production['Share BOF CC']
steel_production['BOF'] = steel_production['BOF CC']+steel_production['BOF MC']    

"""New energy consumption after changing productions routes"""

Energy_consumption_charcoal_increase = energy_consumption('todas')
Total_energy_consumption_charcoal_increase = energy_consumption('todas').groupby(['Combustivel'], axis =0, as_index = False).sum()
Total_energy_consumption_charcoal_increase.loc[10] = Total_energy_consumption_charcoal_increase.sum()
Total_energy_consumption_charcoal_increase = Total_energy_consumption_charcoal_increase.replace(Total_energy_consumption_charcoal_increase.loc[10]['Combustivel'], 'Total')

#-----------------------------------------------------------------------------------------------------------
"""b. Incrasing EAF production"""
for year in np.linspace(2020,2050,2050-2020+1):
    steel_production.loc[year,] = np.nan
    pig_iron_production.loc[year,] = np.nan
    
steel_production['Share BOF CC'][2030] = steel_production['Share BOF CC'][2019]
steel_production['Share BOF CC'][2040] = steel_production['Share BOF CC'][2019]
steel_production['Share BOF CC'][2050] = steel_production['Share BOF CC'][2019]
steel_production['Share BOF CC'] = steel_production['Share BOF CC'].interpolate()

steel_production['Share EAF'][2030] = steel_production['Share EAF'][2019] *EAF_increase[2030]
steel_production['Share EAF'][2040] = steel_production['Share EAF'][2019] *EAF_increase[2040]
steel_production['Share EAF'][2050] = steel_production['Share EAF'][2019] *EAF_increase[2050]
steel_production['Share EAF'] = steel_production['Share EAF'].interpolate()

steel_production['Share BOF MC'] = 1-steel_production['Share EAF']-steel_production['Share BOF CC']
steel_production['Share BOF'] = 1-steel_production['Share EAF']
  
#The independent production of pig iron follows the growth of the steel production

for ano in activity_increase_2019.keys():
    pig_iron_production['Independente CV'][ano] = pig_iron_production['Independente CV'][2019]*activity_increase_2019[ano]

pig_iron_production['Independente CV'] = pig_iron_production['Independente CV'].interpolate()

#Projection of the Total production of Steel:
for ano in activity_increase_2019.keys():
    steel_production['Total'][ano]= steel_production['Total'][2019]*activity_increase_2019[ano]
    
steel_production['Total']= steel_production['Total'].interpolate()

#estimating BOF  and EAF production (Mt):
steel_production['EAF'] = steel_production['Total']*steel_production['Share EAF']
steel_production['BOF MC'] = steel_production['Total']*steel_production['Share BOF MC']
steel_production['BOF CC'] = steel_production['Total']*steel_production['Share BOF CC']
steel_production['BOF'] = steel_production['BOF CC']+steel_production['BOF MC']    

"""New energy consumption after changing productions routes"""

Energy_EAF_increase = energy_consumption('todas')
Total_energy_consumption_EAF_increase = energy_consumption('todas').groupby(['Combustivel'], axis =0, as_index = False).sum()
Total_energy_consumption_EAF_increase.loc[10] = Total_energy_consumption_EAF_increase.sum()
Total_energy_consumption_EAF_increase = Total_energy_consumption_EAF_increase.replace(Total_energy_consumption_EAF_increase.loc[10]['Combustivel'], 'Total')

#----------------------------------------------------------------------------------------------------------
"""c. Energy Consumption after increase Charcoal AND EAF"""

for year in np.linspace(2020,2050,2050-2020+1):
    steel_production.loc[year,] = np.nan
    pig_iron_production.loc[year,] = np.nan
    
steel_production['Share BOF CC'][2030] = steel_production['Share BOF CC'][2019]*charcoal_increase[2030]
steel_production['Share BOF CC'][2040] = steel_production['Share BOF CC'][2019]*charcoal_increase[2040]
steel_production['Share BOF CC'][2050] = steel_production['Share BOF CC'][2019]*charcoal_increase[2050]
steel_production['Share BOF CC'] = steel_production['Share BOF CC'].interpolate()

steel_production['Share EAF'][2030] = steel_production['Share EAF'][2019] *EAF_increase[2030]
steel_production['Share EAF'][2040] = steel_production['Share EAF'][2019] *EAF_increase[2040]
steel_production['Share EAF'][2050] = steel_production['Share EAF'][2019] *EAF_increase[2050]
steel_production['Share EAF'] = steel_production['Share EAF'].interpolate()

steel_production['Share BOF MC'] = 1-steel_production['Share EAF']-steel_production['Share BOF CC']
steel_production['Share BOF'] = 1-steel_production['Share EAF']
    
#The independent production of pig iron follows the growth of the steel production:
for ano in activity_increase_2019.keys():
    pig_iron_production['Independente CV'][ano] = pig_iron_production['Independente CV'][2019]*activity_increase_2019[ano]

pig_iron_production['Independente CV'] = pig_iron_production['Independente CV'].interpolate()

#Projection of the Total production of Steel:
for ano in activity_increase_2019.keys():
    steel_production['Total'][ano]= steel_production['Total'][2019]*activity_increase_2019[ano]    
steel_production['Total']= steel_production['Total'].interpolate()

#estimating BOF  and EAF production (Mt):
steel_production['EAF'] = steel_production['Total']*steel_production['Share EAF']
steel_production['BOF MC'] = steel_production['Total']*steel_production['Share BOF MC']
steel_production['BOF CC'] = steel_production['Total']*steel_production['Share BOF CC']
steel_production['BOF'] = steel_production['BOF CC']+steel_production['BOF MC']    


"""New energy consumption after changing productions routes"""

Energy_consumption_charcoal_EAF_increase = energy_consumption('todas')
Total_energy_consumption_charcoal_EAF_increase = energy_consumption('todas').groupby(['Combustivel'], axis =0, as_index = False).sum()
Total_energy_consumption_charcoal_EAF_increase.loc[10] = Total_energy_consumption_charcoal_EAF_increase.sum()
Total_energy_consumption_charcoal_EAF_increase = Total_energy_consumption_charcoal_EAF_increase.replace(Total_energy_consumption_charcoal_EAF_increase.loc[10]['Combustivel'], 'Total')

#Energy consumption after shifting EAF AND Charcoal by route:
R1_charcoal_EAF_increase = Energy_consumption_charcoal_EAF_increase.loc[Energy_consumption_charcoal_EAF_increase['Rota']=='R1']
R2_charcoal_EAF_increase = Energy_consumption_charcoal_EAF_increase.loc[Energy_consumption_charcoal_EAF_increase['Rota']=='R2']
R3_charcoal_EAF_increase = Energy_consumption_charcoal_EAF_increase.loc[Energy_consumption_charcoal_EAF_increase['Rota']=='R3']
R4_charcoal_EAF_increase = Energy_consumption_charcoal_EAF_increase.loc[Energy_consumption_charcoal_EAF_increase['Rota']=='R4']

"""Cost of increasing the sahre of Charcoal and EAF route"""
#Calcular a diferença no consumo de energia
Energy_mitigated_charcoal_shift = Total_energy_consumption_projected.iloc[:,1:] - Total_energy_consumption_charcoal_increase.iloc[:,1:]
Energy_mitigated_charcoal_shift['Combustivel'] = Total_energy_consumption_projected ['Combustivel']
Energy_mitigated_charcoal_shift = Energy_mitigated_charcoal_shift.drop(index= 10)
colunas = Energy_mitigated_charcoal_shift.columns.tolist()
colunas = colunas[-1:]+colunas[:-1]
Energy_mitigated_charcoal_shift  = Energy_mitigated_charcoal_shift [colunas]

Energy_mitigated_EAF_shift = Total_energy_consumption_projected.iloc[:,1:] - Total_energy_consumption_EAF_increase.iloc[:,1:]
Energy_mitigated_EAF_shift['Combustivel'] = Total_energy_consumption_projected ['Combustivel']
Energy_mitigated_EAF_shift = Energy_mitigated_EAF_shift.drop(index= 10)
colunas = Energy_mitigated_EAF_shift.columns.tolist()
colunas = colunas[-1:]+colunas[:-1]
Energy_mitigated_EAF_shift  = Energy_mitigated_EAF_shift [colunas]

#calcular o custo dessa diferença 
Cost_saved_charcoal_shift = Energy_mitigated_charcoal_shift.copy()
for indice in Cost_saved_charcoal_shift.index:
    Cost_saved_charcoal_shift.loc[indice,'2005':] = Energy_mitigated_charcoal_shift.loc[indice, '2005':]*float(fuel_prices.loc[fuel_prices['Combustivel']==Cost_saved_charcoal_shift.loc[indice]['Combustivel']]['BRL/GJ'])/(10**6)


Cost_saved_EAF_shift = Energy_mitigated_EAF_shift.copy()
for indice in Cost_saved_EAF_shift.index:
    Cost_saved_EAF_shift.loc[indice,'2005':] = Energy_mitigated_EAF_shift.loc[indice, '2005':]*float(fuel_prices.loc[fuel_prices['Combustivel']==Cost_saved_EAF_shift.loc[indice]['Combustivel']]['BRL/GJ'])/(10**6)

Cost_saved_fuel_shift = np.array([Cost_saved_EAF_shift.loc[:,'2005':].sum()])
Cost_saved_fuel_shift = np.append(Cost_saved_fuel_shift, np.array([Cost_saved_charcoal_shift.loc[:,'2005':].sum()]),axis=0)
Cost_saved_fuel_shift = pd.DataFrame(Cost_saved_fuel_shift, columns = Cost_saved_EAF_shift.columns[1:])
Cost_saved_fuel_shift['Medida de mitigicao'] = ['EAF increase','Charcoal increase']
colunas = Cost_saved_fuel_shift.columns.tolist()
colunas = colunas[-1:]+colunas[:-1]
Cost_saved_fuel_shift  = Cost_saved_fuel_shift [colunas]

#%%
"""Energy efficiency and process improvements:"""
#Medida de mitigação (quantidade mitigada, penetração, custo unitário de investiment, custo unitário de operação)

#Creating a DF with the penetration of the mitigation measures:
mitigation_measures_penetration = pd.DataFrame()
mitigation_measures_penetration['Medida de mitigacao'] = mitigation_measures['Medida de mitigacao']
mitigation_measures_penetration['Rota'] = mitigation_measures['Rota']
mitigation_measures_penetration['Etapa'] = mitigation_measures['Etapa']


#Creating the penetration values for each year
for year in projected_years:
    mitigation_measures_penetration[year] = 0

for indice in mitigation_measures.index:
    for ano in projected_years:
         mitigation_measures_penetration.loc[indice,ano] = np.interp(ano,(2020,2050),(0,mitigation_measures.loc[indice,'Penetracao']))

#New Energy Intensity:
for indice in mitigation_measures.index: #pra cada medida de mitigacao
    for year in projected_years: #pra cada ano
        for combustivel in EI_BEU.Combustivel.unique():
            i = EI_BEU.loc[EI_BEU['Rota']==mitigation_measures.loc[indice,'Rota']].loc[EI_BEU['Etapa'] == mitigation_measures.loc[indice,'Etapa']].loc[EI_BEU.Combustivel == combustivel][str(year)]
            EI_BEU.loc[i.index,str(year)] = i-(i/(EI_BEU.loc[EI_BEU['Rota'] ==mitigation_measures.loc[indice,'Rota']].loc[EI_BEU['Etapa'] ==mitigation_measures.loc[indice,'Etapa']][str(year)].sum()))*mitigation_measures.loc[0,'Reducao na intensidade (Gj/t)']*mitigation_measures_penetration.loc[indice,year]
            
#Energy consumption after implemeting the mitigation measures:
Energy_consumption_mitigated = energy_consumption('todas')
Total_energy_consumption_mitigated = energy_consumption('todas').groupby(['Combustivel'], axis =0, as_index = False).sum()
Total_energy_consumption_mitigated.loc[10] = Total_energy_consumption_mitigated.sum()
Total_energy_consumption_mitigated= Total_energy_consumption_mitigated.replace(Total_energy_consumption_mitigated.loc[10]['Combustivel'], 'Total')
    
#%%
"""Estimating the amount of energy mitigated"""

#Estimating the energy mitigated after the change of fuels
Energy_mitigated_by_measures = Energy_consumption_charcoal_EAF_increase.iloc[:,3:]-Energy_consumption_mitigated.iloc[:,3:]

#Creating new columns:
Energy_mitigated_by_measures['Rota'] = EI_BEU['Rota']
Energy_mitigated_by_measures ['Etapa'] = EI_BEU ['Etapa']
Energy_mitigated_by_measures ['Combustivel'] = EI_BEU ['Combustivel']
#adjusting the order of the columns:
colunas = Energy_mitigated_by_measures.columns.tolist()
colunas = colunas[-3:]+colunas[:-3]
Energy_mitigated_by_measures  = Energy_mitigated_by_measures [colunas]

#Amount of energy mitigated in each main Route:
Energy_mitigated_by_measures.loc[Energy_mitigated_by_measures['Rota'] == 'R1'].groupby(['Etapa']).sum() #Energy mitigated by Step in R1
Energy_mitigated_by_measures.loc[Energy_mitigated_by_measures['Rota'] == 'R1'].loc[Energy_mitigated_by_measures['Etapa'] == 'Aciaria'] #Energy mitigated in Aciaria in R1 by fuel

"""Value save from mitigation measures"""

Cost_saved_mitigation_measures = Energy_mitigated_by_measures.copy()
for indice in Cost_saved_mitigation_measures.index:
    Cost_saved_mitigation_measures.loc[indice,'2005':] = Energy_mitigated_by_measures.loc[indice, '2005':]*float(fuel_prices.loc[fuel_prices['Combustivel']==Cost_saved_mitigation_measures.loc[indice]['Combustivel']]['BRL/GJ'])/(10**6)
    
"""Economy by measure"""

custo = np.array([])

for indice in mitigation_measures.index:
    if indice == 0:
        custo = pd.DataFrame(Cost_saved_mitigation_measures.loc[Energy_mitigated_by_measures['Rota'] == mitigation_measures.loc[indice,'Rota']].groupby(['Etapa']).sum()).loc[mitigation_measures.loc[indice,'Etapa']]*mitigation_measures.loc[indice,'Percentual of reduction']
        custo = np.array([custo])
    else:
        x = pd.DataFrame(Cost_saved_mitigation_measures.loc[Energy_mitigated_by_measures['Rota'] == mitigation_measures.loc[indice,'Rota']].groupby(['Etapa']).sum()).loc[mitigation_measures.loc[indice,'Etapa']]*mitigation_measures.loc[indice,'Percentual of reduction']
        x= np.array([x])
        custo = np.append(custo,x,axis = 0)

#Cost saved by measure (fuel saving) in MR$:
cost_saved_by_measure = pd.DataFrame(custo,columns = Cost_saved_mitigation_measures.columns[3:])    
cost_saved_by_measure['Medida de mitigicao'] = mitigation_measures['Medida de mitigacao']
#adjusting the order of the columns:
colunas = cost_saved_by_measure.columns.tolist()
colunas = colunas[-1:]+colunas[:-1]
cost_saved_by_measure  = cost_saved_by_measure [colunas]

#%%
"""Emissions in the mitigated scenario"""
#Calcular as emissões da substituição

#Emissions after shifting for Charcoal
Emissions_charcoal_shift_CO2 = emission_process_calc(Total_energy_consumption_charcoal_increase,steel_production['Total'],'CO2',process_fuels).sum()+emission_energy_calc(Total_energy_consumption_charcoal_increase,'CO2',energy_fuels).sum()
Emissions_charcoal_shift_CH4 = emission_process_calc(Total_energy_consumption_charcoal_increase,steel_production['Total'],'CH4',process_fuels).sum()+emission_energy_calc(Total_energy_consumption_charcoal_increase,'CH4',energy_fuels).sum()
Emissions_charcoal_shift_N2O = emission_process_calc(Total_energy_consumption_charcoal_increase,steel_production['Total'],'N2O',process_fuels).sum()+emission_energy_calc(Total_energy_consumption_charcoal_increase,'N2O',energy_fuels).sum()

#Emissions after shifting of EAF
Emissions_EAF_shift_CO2 = emission_process_calc(Total_energy_consumption_EAF_increase,steel_production['Total'],'CO2',process_fuels).sum()+emission_energy_calc(Total_energy_consumption_EAF_increase,'CO2',energy_fuels).sum()
Emissions_EAF_shift_CH4 = emission_process_calc(Total_energy_consumption_EAF_increase,steel_production['Total'],'CH4',process_fuels).sum()+emission_energy_calc(Total_energy_consumption_EAF_increase,'CH4',energy_fuels).sum()
Emissions_EAF_shift_N2O = emission_process_calc(Total_energy_consumption_EAF_increase,steel_production['Total'],'N2O',process_fuels).sum()+emission_energy_calc(Total_energy_consumption_EAF_increase,'N2O',energy_fuels).sum()

#Emissions after shifting EAF AND Charcoal:
Emissions_charcoal_EAF_shift_CO2 = emission_process_calc(Total_energy_consumption_charcoal_EAF_increase,steel_production['Total'],'CO2',process_fuels).sum()+emission_energy_calc(Total_energy_consumption_charcoal_EAF_increase,'CO2',energy_fuels).sum()
Emissions_charcoal_EAF_shift_CH4 = emission_process_calc(Total_energy_consumption_charcoal_EAF_increase,steel_production['Total'],'CH4',process_fuels).sum()+emission_energy_calc(Total_energy_consumption_charcoal_EAF_increase,'CH4',energy_fuels).sum()
Emissions_charcoal_EAF_shift_N2O = emission_process_calc(Total_energy_consumption_charcoal_EAF_increase,steel_production['Total'],'N2O',process_fuels).sum()+emission_energy_calc(Total_energy_consumption_charcoal_EAF_increase,'N2O',energy_fuels).sum()

def total_emissions_by_step(energy_consumption,production,GHG):
    """This function estimates the total emissions for a given energy consumption, production and GHG"""
    emission_process = emission_process_calc(energy_consumption,production,GHG,process_fuels)
    emission_energy = emission_energy_calc(energy_consumption,GHG,energy_fuels)
    emission_total = emission_process.append(emission_energy)
    emission_total['Etapa'] = energy_consumption.Etapa[emission_total.index]
    emission_total = emission_total.groupby(['Etapa']).sum()
    return emission_total

#Emissions  by route after changing the share of Charcoal and EAF:
Emissions_R1_charcoal_EAF_increase_CO2 =total_emissions_by_step(R1_charcoal_EAF_increase,steel_production['BOF MC'],'CO2')
Emissions_R1_charcoal_EAF_increase_CH4 =total_emissions_by_step(R1_charcoal_EAF_increase,steel_production['BOF MC'],'CH4')
Emissions_R1_charcoal_EAF_increase_N2O =total_emissions_by_step(R1_charcoal_EAF_increase,steel_production['BOF MC'],'N2O')

Emissions_R2_charcoal_EAF_increase_CO2 =total_emissions_by_step(R2_charcoal_EAF_increase,steel_production['BOF CC'],'CO2')
Emissions_R2_charcoal_EAF_increase_CH4 =total_emissions_by_step(R2_charcoal_EAF_increase,steel_production['BOF CC'],'CH4')
Emissions_R2_charcoal_EAF_increase_N2O =total_emissions_by_step(R2_charcoal_EAF_increase,steel_production['BOF CC'],'N2O')

Emissions_R3_charcoal_EAF_increase_CO2 =total_emissions_by_step(R3_charcoal_EAF_increase,steel_production['EAF'],'CO2')
Emissions_R3_charcoal_EAF_increase_CH4 =total_emissions_by_step(R3_charcoal_EAF_increase,steel_production['EAF'],'CH4')
Emissions_R3_charcoal_EAF_increase_N2O =total_emissions_by_step(R3_charcoal_EAF_increase,steel_production['EAF'],'N2O')

Emissions_R4_charcoal_EAF_increase_CO2 =total_emissions_by_step(R4_charcoal_EAF_increase,pig_iron_production['Independente CV'],'CO2')
Emissions_R4_charcoal_EAF_increase_CH4 =total_emissions_by_step(R4_charcoal_EAF_increase,pig_iron_production['Independente CV'],'CH4')
Emissions_R4_charcoal_EAF_increase_N2O =total_emissions_by_step(R4_charcoal_EAF_increase,pig_iron_production['Independente CV'],'N2O')

#Energy consumption of each route after implementing mitigation measures in each Route:
R1_energy_mitigated = Energy_consumption_mitigated.loc[Energy_consumption_mitigated['Rota']=='R1']
R2_energy_mitigated = Energy_consumption_mitigated.loc[Energy_consumption_mitigated['Rota']=='R2']
R3_energy_mitigated = Energy_consumption_mitigated.loc[Energy_consumption_mitigated['Rota']=='R3']
R4_energy_mitigated = Energy_consumption_mitigated.loc[Energy_consumption_mitigated['Rota']=='R4']

#Emissions of each route after implemeting the mitigation measures:
Emissions_R1_mitigated_CO2 = total_emissions_by_step(R1_energy_mitigated,steel_production['BOF MC'],'CO2')
Emissions_R1_mitigated_CH4 = total_emissions_by_step(R1_energy_mitigated,steel_production['BOF MC'],'CH4')
Emissions_R1_mitigated_N2O = total_emissions_by_step(R1_energy_mitigated,steel_production['BOF MC'],'N2O')

Emissions_R2_mitigated_CO2 = total_emissions_by_step(R2_energy_mitigated,steel_production['BOF CC'],'CO2')
Emissions_R2_mitigated_CH4 = total_emissions_by_step(R2_energy_mitigated,steel_production['BOF CC'],'CH4')
Emissions_R2_mitigated_N2O = total_emissions_by_step(R2_energy_mitigated,steel_production['BOF CC'],'N2O')

Emissions_R3_mitigated_CO2 = total_emissions_by_step(R3_energy_mitigated,steel_production['EAF'],'CO2')
Emissions_R3_mitigated_CH4 = total_emissions_by_step(R3_energy_mitigated,steel_production['EAF'],'CH4')
Emissions_R3_mitigated_N2O = total_emissions_by_step(R3_energy_mitigated,steel_production['EAF'],'N2O')

Emissions_R4_mitigated_CO2 = total_emissions_by_step(R4_energy_mitigated,pig_iron_production['Independente CV'],'CO2')
Emissions_R4_mitigated_CH4 = total_emissions_by_step(R4_energy_mitigated,pig_iron_production['Independente CV'],'CH4')
Emissions_R4_mitigated_N2O = total_emissions_by_step(R4_energy_mitigated,pig_iron_production['Independente CV'],'N2O')

Emissions_mitigation_scenario_CO2 = Emissions_R1_mitigated_CO2.sum()+Emissions_R2_mitigated_CO2.sum()+Emissions_R3_mitigated_CO2.sum()+Emissions_R4_mitigated_CO2.sum()
Emissions_mitigation_scenario_CH4 = Emissions_R1_mitigated_CH4.sum()+Emissions_R2_mitigated_CH4.sum()+Emissions_R3_mitigated_CH4.sum()+Emissions_R4_mitigated_CH4.sum()
Emissions_mitigation_scenario_N2O = Emissions_R1_mitigated_N2O.sum()+Emissions_R2_mitigated_N2O.sum()+Emissions_R3_mitigated_N2O.sum()+Emissions_R4_mitigated_N2O.sum()


#"""Mitigated emission by measure"""
##Mitigated Emission by route
Emissions_mitigated_by_R1_CO2=Emissions_R1_charcoal_EAF_increase_CO2 - Emissions_R1_mitigated_CO2   
Emissions_mitigated_by_R1_CH4=Emissions_R1_charcoal_EAF_increase_CH4- Emissions_R1_mitigated_CH4
Emissions_mitigated_by_R1_N2O=Emissions_R1_charcoal_EAF_increase_N2O - Emissions_R1_mitigated_N2O

Emissions_mitigated_by_R2_CO2=Emissions_R2_charcoal_EAF_increase_CO2 - Emissions_R2_mitigated_CO2
Emissions_mitigated_by_R2_CH4=Emissions_R2_charcoal_EAF_increase_CH4- Emissions_R2_mitigated_CH4
Emissions_mitigated_by_R2_N2O=Emissions_R2_charcoal_EAF_increase_N2O - Emissions_R2_mitigated_N2O

Emissions_mitigated_by_R3_CO2=Emissions_R3_charcoal_EAF_increase_CO2 - Emissions_R3_mitigated_CO2
Emissions_mitigated_by_R3_CH4=Emissions_R3_charcoal_EAF_increase_CH4- Emissions_R3_mitigated_CH4
Emissions_mitigated_by_R3_N2O=Emissions_R3_charcoal_EAF_increase_N2O - Emissions_R3_mitigated_N2O

Emissions_mitigated_by_R4_CO2=Emissions_R4_charcoal_EAF_increase_CO2 - Emissions_R4_mitigated_CO2
Emissions_mitigated_by_R4_CH4=Emissions_R4_charcoal_EAF_increase_CH4- Emissions_R4_mitigated_CH4
Emissions_mitigated_by_R4_N2O=Emissions_R4_charcoal_EAF_increase_N2O - Emissions_R4_mitigated_N2O



#Mitigated emission by measure
#Emissions_mitigated_by_measure_CO2 = pd.DataFrame(columns =Total_energy_consumption_projected.columns[1:])
#Emissions_mitigated_by_measure_CO2['Medida de mitigacao']= mitigation_measures['Medida de mitigacao']
#Emissions_mitigated_by_measure_CO2['Rota']= mitigation_measures['Rota']
#colunas = Emissions_mitigated_by_measure_CO2.columns.tolist()
#colunas = colunas[-2:]+colunas[:-2]
#Emissions_mitigated_by_measure_CO2  = Emissions_mitigated_by_measure_CO2[colunas]

#Emissions mitigated by measure CO2
Emissions_mitigated_by_measure_CO2 = pd.DataFrame(columns =Emissions_mitigated_by_R1_CO2.columns)
for medida in mitigation_measures.index:
    if mitigation_measures.loc[medida,'Rota'] == 'R1':
        a=float(mitigation_measures.loc[medida,'Percentual of reduction'])*Emissions_mitigated_by_R1_CO2.loc[mitigation_measures.loc[medida,'Etapa']]
        Emissions_mitigated_by_measure_CO2=Emissions_mitigated_by_measure_CO2.append(a)
    elif mitigation_measures.loc[medida,'Rota']== 'R2':
        a=float(mitigation_measures.loc[medida,'Percentual of reduction'])*Emissions_mitigated_by_R2_CO2.loc[mitigation_measures.loc[medida,'Etapa']]
        Emissions_mitigated_by_measure_CO2=Emissions_mitigated_by_measure_CO2.append(a)
    elif mitigation_measures.loc[medida,'Rota']== 'R3':
        a=float(mitigation_measures.loc[medida,'Percentual of reduction'])*Emissions_mitigated_by_R3_CO2.loc[mitigation_measures.loc[medida,'Etapa']]
        Emissions_mitigated_by_measure_CO2=Emissions_mitigated_by_measure_CO2.append(a)
    elif mitigation_measures.loc[medida,'Rota'] == 'R4':
        a=float(mitigation_measures.loc[medida,'Percentual of reduction'])*Emissions_mitigated_by_R4_CO2.loc[mitigation_measures.loc[medida,'Etapa']]
        Emissions_mitigated_by_measure_CO2=Emissions_mitigated_by_measure_CO2.append(a)
Emissions_mitigated_by_measure_CO2.index = mitigation_measures.index       
Emissions_mitigated_by_measure_CO2['Etapa']  = mitigation_measures.Etapa
Emissions_mitigated_by_measure_CO2['Rota']  = mitigation_measures.Rota
Emissions_mitigated_by_measure_CO2['Medida de mitigacao']=mitigation_measures['Medida de mitigacao']

#Emissions mitigated by measure CH4
Emissions_mitigated_by_measure_CH4 = pd.DataFrame(columns =Emissions_mitigated_by_R1_CH4.columns)
for medida in mitigation_measures['Medida de mitigacao']:
    if mitigation_measures.loc[mitigation_measures['Medida de mitigacao'] == medida]['Rota'].any() == 'R1':
        a=float( mitigation_measures.loc[mitigation_measures['Medida de mitigacao'] == medida].loc[mitigation_measures.Rota == 'R1','Percentual of reduction'])*Emissions_mitigated_by_R1_CH4.loc[mitigation_measures.loc[mitigation_measures['Medida de mitigacao']== medida].loc[mitigation_measures.Rota == 'R1','Etapa']]
        Emissions_mitigated_by_measure_CH4=Emissions_mitigated_by_measure_CH4.append(a)
    elif mitigation_measures.loc[mitigation_measures['Medida de mitigacao'] == medida]['Rota'].any() == 'R2':
        a=float( mitigation_measures.loc[mitigation_measures['Medida de mitigacao'] == medida].loc[mitigation_measures.Rota == 'R2','Percentual of reduction'])*Emissions_mitigated_by_R2_CH4.loc[mitigation_measures.loc[mitigation_measures['Medida de mitigacao']== medida].loc[mitigation_measures.Rota == 'R2','Etapa']]
        Emissions_mitigated_by_measure_CH4=Emissions_mitigated_by_measure_CH4.append(a)
    elif mitigation_measures.loc[mitigation_measures['Medida de mitigacao'] == medida]['Rota'].any() == 'R3':
        a=float( mitigation_measures.loc[mitigation_measures['Medida de mitigacao'] == medida].loc[mitigation_measures.Rota == 'R3','Percentual of reduction'])*Emissions_mitigated_by_R3_CH4.loc[mitigation_measures.loc[mitigation_measures['Medida de mitigacao']== medida].loc[mitigation_measures.Rota == 'R3','Etapa']]
        Emissions_mitigated_by_measure_CH4=Emissions_mitigated_by_measure_CH4.append(a)
    elif mitigation_measures.loc[mitigation_measures['Medida de mitigacao'] == medida]['Rota'].any() == 'R4':
        a=float( mitigation_measures.loc[mitigation_measures['Medida de mitigacao'] == medida].loc[mitigation_measures.Rota == 'R4','Percentual of reduction'])*Emissions_mitigated_by_R4_CH4.loc[mitigation_measures.loc[mitigation_measures['Medida de mitigacao']== medida].loc[mitigation_measures.Rota == 'R4','Etapa']]
        Emissions_mitigated_by_measure_CH4=Emissions_mitigated_by_measure_CH4.append(a)
Emissions_mitigated_by_measure_CH4.index = mitigation_measures.index       
Emissions_mitigated_by_measure_CH4['Etapa']  = mitigation_measures.Etapa
Emissions_mitigated_by_measure_CH4['Rota']  = mitigation_measures.Rota
Emissions_mitigated_by_measure_CH4['Medida de mitigacao']=mitigation_measures['Medida de mitigacao']

#Emissions mitigated by measure N2O
Emissions_mitigated_by_measure_N2O = pd.DataFrame(columns =Emissions_mitigated_by_R1_N2O.columns)
for medida in mitigation_measures['Medida de mitigacao']:
    if mitigation_measures.loc[mitigation_measures['Medida de mitigacao'] == medida]['Rota'].any() == 'R1':
        a=float( mitigation_measures.loc[mitigation_measures['Medida de mitigacao'] == medida].loc[mitigation_measures.Rota == 'R1','Percentual of reduction'])*Emissions_mitigated_by_R1_N2O.loc[mitigation_measures.loc[mitigation_measures['Medida de mitigacao']== medida].loc[mitigation_measures.Rota == 'R1','Etapa']]
        Emissions_mitigated_by_measure_N2O=Emissions_mitigated_by_measure_N2O.append(a)
    elif mitigation_measures.loc[mitigation_measures['Medida de mitigacao'] == medida]['Rota'].any() == 'R2':
        a=float( mitigation_measures.loc[mitigation_measures['Medida de mitigacao'] == medida].loc[mitigation_measures.Rota == 'R2','Percentual of reduction'])*Emissions_mitigated_by_R2_N2O.loc[mitigation_measures.loc[mitigation_measures['Medida de mitigacao']== medida].loc[mitigation_measures.Rota == 'R2','Etapa']]
        Emissions_mitigated_by_measure_N2O=Emissions_mitigated_by_measure_N2O.append(a)
    elif mitigation_measures.loc[mitigation_measures['Medida de mitigacao'] == medida]['Rota'].any() == 'R3':
        a=float( mitigation_measures.loc[mitigation_measures['Medida de mitigacao'] == medida].loc[mitigation_measures.Rota == 'R3','Percentual of reduction'])*Emissions_mitigated_by_R3_N2O.loc[mitigation_measures.loc[mitigation_measures['Medida de mitigacao']== medida].loc[mitigation_measures.Rota == 'R3','Etapa']]
        Emissions_mitigated_by_measure_N2O=Emissions_mitigated_by_measure_N2O.append(a)
    elif mitigation_measures.loc[mitigation_measures['Medida de mitigacao'] == medida]['Rota'].any() == 'R4':
        a=float( mitigation_measures.loc[mitigation_measures['Medida de mitigacao'] == medida].loc[mitigation_measures.Rota == 'R4','Percentual of reduction'])*Emissions_mitigated_by_R4_N2O.loc[mitigation_measures.loc[mitigation_measures['Medida de mitigacao']== medida].loc[mitigation_measures.Rota == 'R4','Etapa']]
        Emissions_mitigated_by_measure_N2O=Emissions_mitigated_by_measure_N2O.append(a)
Emissions_mitigated_by_measure_N2O.index = mitigation_measures.index       
Emissions_mitigated_by_measure_N2O['Etapa']  = mitigation_measures.Etapa
Emissions_mitigated_by_measure_N2O['Rota']  = mitigation_measures.Rota
Emissions_mitigated_by_measure_N2O['Medida de mitigacao']=mitigation_measures['Medida de mitigacao']

#%%
"""Investiment and operational costs"""
#É o CAPEX ou OPEX x a produção de cada uma das rotas

"""CAPEX"""
route_name = {'R1':'BOF MC','R2':'BOF CC',"R3": "EAF","R4": "Independente CV"}

for indice in mitigation_measures.index:
    if indice == 0:
        capex = (mitigation_measures.loc[indice,'CAPEX (RS/t)']*steel_production.loc[2020:,route_name[mitigation_measures.loc[indice,'Rota']]]*mitigation_measures_penetration.iloc[indice,3:]).tolist()
        capex = np.array([capex])
    else:
        if mitigation_measures.loc[indice,'Rota'] == 'R4':
            x = (mitigation_measures.loc[indice,'CAPEX (RS/t)']*pig_iron_production.loc[2020:,route_name[mitigation_measures.loc[indice,'Rota']]]*mitigation_measures_penetration.iloc[indice,3:]).tolist()
            x= np.array([x])
            capex = np.append(capex,x,axis=0)
        else:
            x = (mitigation_measures.loc[indice,'CAPEX (RS/t)']*steel_production.loc[2020:,route_name[mitigation_measures.loc[indice,'Rota']]]*mitigation_measures_penetration.iloc[indice,3:]).tolist()
            x= np.array([x])
            capex = np.append(capex,x,axis = 0)

Total_capex = pd.DataFrame(capex/(10**6), columns = projected_years) #dividi por milhões pra ter o capex em milhões de reais
Total_capex['Meidade de mitigicao'] = mitigation_measures['Medida de mitigacao']
#adjusting the order of the columns:
colunas = Total_capex.columns.tolist()
colunas = colunas[-1:]+colunas[:-1]
Total_capex  = Total_capex [colunas]

"""OPEX"""
for indice in mitigation_measures.index:
    if indice == 0:
        opex = (mitigation_measures.loc[indice,'OPEX (RS/t)']*steel_production.loc[2020:,route_name[mitigation_measures.loc[indice,'Rota']]]*mitigation_measures_penetration.iloc[indice,3:]).tolist()
        opex = np.array([opex])
    else:
        if mitigation_measures.loc[indice,'Rota'] == 'R4':
            x = (mitigation_measures.loc[indice,'OPEX (RS/t)']*pig_iron_production.loc[2020:,route_name[mitigation_measures.loc[indice,'Rota']]]*mitigation_measures_penetration.iloc[indice,3:]).tolist()
            x= np.array([x])
            opex = np.append(opex,x,axis=0)
        else:
            x = (mitigation_measures.loc[indice,'OPEX (RS/t)']*steel_production.loc[2020:,route_name[mitigation_measures.loc[indice,'Rota']]]*mitigation_measures_penetration.iloc[indice,3:]).tolist()
            x= np.array([x])
            opex = np.append(opex,x,axis = 0)

Total_opex = pd.DataFrame(opex/(10**6), columns = projected_years) #dividi por milhões pra ter o opex em milhões de reais
Total_opex['Meidade de mitigicao'] = mitigation_measures['Medida de mitigacao']
#adjusting the order of the columns:
colunas = Total_opex.columns.tolist()
colunas = colunas[-1:]+colunas[:-1]
Total_opex  = Total_opex [colunas]

#%%

"""Consolidation"""

#Energy consumption in BAU and Mitigated scenario:
#Figure_energy_consumption_projected = plt.plot(Energy_consumption_projected.loc[:,'2005':].sum())
#Figure_energy_consumption_mitigated = plt.plot(Energy_consumption_mitigated.loc[:,'2005':].sum())

#Emissions:
Figure_emissions_projected = plt.plot(Emissions_projected_CO2)
Figure_emissions_fuel = plt.plot(Emissions_charcoal_EAF_shift_CO2)
Figure_emission_mitigation_measures = plt.plot(Emissions_mitigation_scenario_CO2)
