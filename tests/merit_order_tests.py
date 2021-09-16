import pandas as pd

from utils.data_utils import s3BucketManager
from grid.portfolios import Portfolio
from grid.asset_group_optimisation import MeritOrderOptimiser
from grid_resources.dispatchable_generator_technologies import GeneratorTechnoEconomicProperties, GeneratorTechnology
from grid_resources.commodities import Fuel, StaticPrice, Markets, Emissions
from grid_resources.curves import StochasticAnnualCurve
from matplotlib import pyplot as plt
from time import time

bucket = s3BucketManager('jw-modelling')
folders = ['colombia-portfolio-inputs']

generators_fn = 'generator_economics.json'
demand_fn = 'UnitDemand2013.json'
fuels_fn = 'test_fuels.json'
coal_gas_diesel_data_fn = 'coal_gas_diesel_prices_dollars_per_mwh_monthly.csv'

generator_economics = bucket.s3_json_to_dict(folders, generators_fn)
demand = bucket.s3_json_to_dict(folders, demand_fn)
fuels_data = bucket.s3_json_to_dict(folders, fuels_fn)
coal_gas_diesel_monthly = bucket.s3_csv_to_df(folders, coal_gas_diesel_data_fn)

emissions_tariff = Emissions('carbon_price', 100, '$ / tonne')
interest_rate = 0.03
demand = StochasticAnnualCurve(
    'test',
    'MWh',
    pd.Series(demand['demand'], index=range(len(demand['demand'])))
)

print(fuels_data)
fuels_dict = {}
for fuel in fuels_data['fuels']:
    fuels_dict[fuel['name']] = Fuel(**fuel)


generators = []
for gen, data in generator_economics.items():
    if gen != 'Existing Hydro':
        generators.append(
            GeneratorTechnology(
                gen,
                properties=GeneratorTechnoEconomicProperties.from_dict(
                    gen,
                    data,
                    fuels_dict,
                    emissions_tariff,
                    interest_rate
                ),
            )
        )
print(generators)

print(fuels_dict)

static_price_models = StaticPrice({
    'gas': fuels_dict['gas'],
    'biomass': fuels_dict['biomass'],
    'water': fuels_dict['water'],
    'coal': fuels_dict['coal'],
    'diesel': fuels_dict['diesel']
})

fuel_markets = Markets(
    [static_price_models]
)

start = time()
merit_order_portfolio = Portfolio.build_portfolio(
    generators,
    [],
    demand,
    MeritOrderOptimiser('merit_order'),
    fuel_markets
)

merit_order_portfolio.plot_cost_curves()
merit_order_portfolio.plot_ldc()
dispatch = merit_order_portfolio.dispatch()
merit_order_portfolio.plot_dispatch()
plt.show()