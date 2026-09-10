"""Reviewed seed ontology from the 2025 and 2026 NBS specification tables.

This module is data, not a claim that the full historical acquisition is complete.  Dates
before the two documented basket snapshots remain to be established from the Chinese
release archive.
"""

from __future__ import annotations

from dataclasses import dataclass


SOURCE_2025 = "https://www.stats.gov.cn/english/PressRelease/202509/t20250915_1961186.html"
SOURCE_2026 = "https://www.stats.gov.cn/english/PressRelease/202601/t20260115_1962308.html"


CATEGORIES = {
    "ferrous_metals": ("黑色金属", "Ferrous metals", "processed_industrial_material", "PPI_C31"),
    "nonferrous_metals": ("有色金属", "Nonferrous metals", "processed_industrial_material", "PPI_C32"),
    "chemicals": ("化工产品", "Chemical products", "intermediate_input", "PPI_C26"),
    "petroleum_gas": ("石油天然气", "Petroleum and gas", "energy_input", "PPI_C25"),
    "coal": ("煤炭", "Coal", "raw_material_energy", "PPI_B06"),
    "nonmetallic": ("非金属矿产品", "Non-metallic mineral products", "processed_industrial_material", "PPI_C30"),
    "agricultural": ("农产品", "Agricultural products for processing", "raw_material", "PPI_C13"),
    "ag_inputs": ("农业生产资料", "Agricultural means of production", "intermediate_input", "PPI_C26"),
    "forest": ("林产品", "Forest products", "raw_and_processed_material", "PPI_C22"),
}


@dataclass(frozen=True)
class ProductSeed:
    slug: str
    name_zh: str
    name_en: str
    specification: str
    unit: str
    family: str
    category: str
    ppi_industry: str


# The 50-product basket documented in the September 2025 specification table.
PRODUCTS_2025 = [
    ProductSeed("rebar_hrb400e_20mm", "螺纹钢", "Rebar", "Φ20mm, HRB400E", "tonne", "rebar", "ferrous_metals", "PPI_C31"),
    ProductSeed("wire_hpb300_8_10mm", "线材", "Wire", "Φ8-10mm, HPB300", "tonne", "steel_long_products", "ferrous_metals", "PPI_C31"),
    ProductSeed("medium_plate_q235_20mm", "普通中板", "Ordinary Medium Plate", "20mm, Q235", "tonne", "steel_flat_products", "ferrous_metals", "PPI_C31"),
    ProductSeed("hot_rolled_sheet_q235", "热轧普通板卷", "Ordinary Hot-Rolled Sheet", "4.75-11.5mm, Q235, width 1500mm", "tonne", "steel_flat_products", "ferrous_metals", "PPI_C31"),
    ProductSeed("seamless_pipe_20_219x6", "无缝钢管", "Seamless Steel Pipe", "219*6, 20#", "tonne", "steel_pipe", "ferrous_metals", "PPI_C31"),
    ProductSeed("angle_steel_5", "角钢", "Angle Steel", "5#", "tonne", "steel_sections", "ferrous_metals", "PPI_C31"),
    ProductSeed("electrolytic_copper_1", "电解铜", "Electrolytic Copper", "1#", "tonne", "copper", "nonferrous_metals", "PPI_C32"),
    ProductSeed("aluminum_ingot_a00", "铝锭", "Aluminum Ingot", "A00", "tonne", "aluminum", "nonferrous_metals", "PPI_C32"),
    ProductSeed("lead_ingot_1", "铅锭", "Lead Ingot", "1#", "tonne", "lead", "nonferrous_metals", "PPI_C32"),
    ProductSeed("zinc_ingot_0", "锌锭", "Zinc Ingot", "0#", "tonne", "zinc", "nonferrous_metals", "PPI_C32"),
    ProductSeed("sulfuric_acid_98", "硫酸", "Sulfuric Acid", "98%", "tonne", "sulfuric_acid", "chemicals", "PPI_C26"),
    ProductSeed("caustic_soda_32", "烧碱", "Caustic Soda", "liquid caustic soda, 32%", "tonne", "chlor_alkali", "chemicals", "PPI_C26"),
    ProductSeed("methanol_superior", "甲醇", "Methyl Alcohol", "superior quality", "tonne", "methanol", "chemicals", "PPI_C26"),
    ProductSeed("benzene_industrial", "纯苯", "Pure Benzene", "petroleum benzene, industrial grade", "tonne", "aromatics", "chemicals", "PPI_C26"),
    ProductSeed("styrene_first_grade", "苯乙烯", "Styrene", "first grade", "tonne", "aromatics_derivatives", "chemicals", "PPI_C26"),
    ProductSeed("polyethylene_lldpe_mi2", "聚乙烯", "Polyethylene", "LLDPE, melt index 2 film material", "tonne", "polyethylene", "chemicals", "PPI_C26"),
    ProductSeed("polypropylene_drawing", "聚丙烯", "Polypropylene", "wire drawing material", "tonne", "polypropylene", "chemicals", "PPI_C26"),
    ProductSeed("pvc_sg5", "聚氯乙烯", "Polyvinyl Chloride", "SG5", "tonne", "polyvinyl_chloride", "chemicals", "PPI_C26"),
    ProductSeed("butadiene_rubber_br9000", "顺丁胶", "Butadiene Rubber", "BR9000", "tonne", "synthetic_rubber", "chemicals", "PPI_C26"),
    ProductSeed("polyester_filament_poy150d48f", "涤纶长丝", "Polyester Filament", "POY150D/48F", "tonne", "polyester_fibre", "chemicals", "PPI_C28"),
    ProductSeed("lng", "液化天然气", "Liquefied Natural Gas", "LNG", "tonne", "natural_gas", "petroleum_gas", "PPI_D45"),
    ProductSeed("lpg", "液化石油气", "Liquefied Petroleum Gas", "LPG", "tonne", "liquefied_petroleum_gas", "petroleum_gas", "PPI_C25"),
    ProductSeed("gasoline_95_vi", "汽油", "Gasoline", "95#, National VI emission standard", "tonne", "motor_gasoline", "petroleum_gas", "PPI_C25"),
    ProductSeed("gasoline_92_vi", "汽油", "Gasoline", "92#, National VI emission standard", "tonne", "motor_gasoline", "petroleum_gas", "PPI_C25"),
    ProductSeed("diesel_0_vi", "柴油", "Diesel Oil", "0#, National VI emission standard", "tonne", "diesel", "petroleum_gas", "PPI_C25"),
    ProductSeed("paraffin_58_semi", "石蜡", "Paraffin", "58#, semi-refined", "tonne", "paraffin", "petroleum_gas", "PPI_C25"),
    ProductSeed("anthracite_washed_medium", "无烟煤", "Anthracite", "washed, medium pieces", "tonne", "anthracite", "coal", "PPI_B06"),
    ProductSeed("mixed_coal_4500", "普通混煤", "Ordinary Mixed Coal", "4500 kilocalories", "tonne", "thermal_coal", "coal", "PPI_B06"),
    ProductSeed("shanxi_mixed_coal_5000", "山西大混", "Shanxi Mixed Coal", "5000 kilocalories", "tonne", "thermal_coal", "coal", "PPI_B06"),
    ProductSeed("shanxi_superior_mixed_5500", "山西优混", "Shanxi Superior Mixed Coal", "5500 kilocalories", "tonne", "thermal_coal", "coal", "PPI_B06"),
    ProductSeed("datong_mixed_coal_5800", "大同混煤", "Datong Mixed Coal", "5800 kilocalories", "tonne", "thermal_coal", "coal", "PPI_B06"),
    ProductSeed("coking_coal_main", "焦煤", "Coking Coal", "main coking coal", "tonne", "coking_coal", "coal", "PPI_B06"),
    ProductSeed("coke_quasi_primary", "焦炭", "Coke", "quasi-primary metallurgical coke", "tonne", "coke", "coal", "PPI_C25"),
    ProductSeed("portland_cement_425_bag", "普通硅酸盐水泥", "Ordinary Portland Cement", "P.O 42.5 in bags", "tonne", "portland_cement", "nonmetallic", "PPI_C30"),
    ProductSeed("portland_cement_425_bulk", "普通硅酸盐水泥", "Ordinary Portland Cement", "P.O 42.5 in bulk", "tonne", "portland_cement", "nonmetallic", "PPI_C30"),
    ProductSeed("float_glass_4_8_5mm", "浮法平板玻璃", "Float Flat Glass", "4.8/5mm", "tonne", "float_glass", "nonmetallic", "PPI_C30"),
    ProductSeed("rice_japonica", "稻米", "Rice", "japonica rice", "tonne", "rice", "agricultural", "PPI_C13"),
    ProductSeed("wheat_grade_3", "小麦", "Wheat", "National Standard Grade III", "tonne", "wheat", "agricultural", "PPI_C13"),
    ProductSeed("corn_yellow_grade_2", "玉米", "Corn", "yellow corn Grade II", "tonne", "corn", "agricultural", "PPI_C13"),
    ProductSeed("cotton_white_grade_3", "棉花", "Cotton (Ginned Cotton)", "white cotton Grade III", "tonne", "cotton", "agricultural", "PPI_C17"),
    ProductSeed("live_hog_three_way", "生猪", "Live Hog", "three-way crossbred", "kg", "live_hog", "agricultural", "PPI_C13"),
    ProductSeed("soybean", "大豆", "Soybean", "soy", "tonne", "soybean", "agricultural", "PPI_C13"),
    ProductSeed("soybean_meal_cp43", "豆粕", "Soybean Meal", "crude protein content≥43%", "tonne", "soybean_meal", "agricultural", "PPI_C13"),
    ProductSeed("peanut_oil", "花生", "Peanut", "for oil processing", "tonne", "peanut", "agricultural", "PPI_C13"),
    ProductSeed("urea_small_medium", "尿素", "Urea", "small and medium granules", "tonne", "nitrogen_fertilizer", "ag_inputs", "PPI_C26"),
    ProductSeed("compound_fertilizer_k2so4_45", "复合肥", "Compound Fertilizer", "potassium sulfate compound fertilizer, NPK 45%", "tonne", "compound_fertilizer", "ag_inputs", "PPI_C26"),
    ProductSeed("glyphosate_95", "农药", "Pesticide (Glyphosate)", "95% technical material", "tonne", "pesticides", "ag_inputs", "PPI_C26"),
    ProductSeed("natural_rubber_scrwf", "天然橡胶", "Natural Rubber", "standard rubber SCRWF", "tonne", "natural_rubber", "forest", "PPI_C29"),
    ProductSeed("pulp_imported_coniferous", "纸浆", "Pulp", "imported coniferous pulp", "tonne", "wood_pulp", "forest", "PPI_C22"),
    ProductSeed("corrugated_paper_aa_120g", "瓦楞纸", "Corrugated Paper", "AA grade, 120g", "tonne", "paper", "forest", "PPI_C22"),
]


REMOVED_2026 = {
    "styrene_first_grade", "pvc_sg5", "gasoline_92_vi", "portland_cement_425_bag",
    "mixed_coal_4500", "shanxi_mixed_coal_5000", "datong_mixed_coal_5800",
}

ADDED_2026 = [
    ProductSeed("ethyl_alcohol_95", "乙醇", "Ethyl Alcohol", "95.0%", "tonne", "ethanol", "chemicals", "PPI_C26"),
    ProductSeed("glacial_acetic_acid_995", "冰醋酸", "Glacial Acetic Acid", "99.5% and above", "tonne", "acetic_acid", "chemicals", "PPI_C26"),
    ProductSeed("lfp_standard_power", "磷酸铁锂", "Lithium Iron Phosphate", "standard power grade", "tonne", "battery_materials", "chemicals", "PPI_C26"),
    ProductSeed("polysilicon_dense", "多晶硅", "Polysilicon", "dense grade, purity 6N-9N", "kg", "solar_materials", "nonmetallic", "PPI_C30"),
    ProductSeed("white_sugar_grade_1", "白砂糖", "White Sugar", "National Standard Grade I", "tonne", "sugar", "agricultural", "PPI_C13"),
    ProductSeed("map_55", "磷肥", "Phosphate Fertilizer", "55% monoammonium phosphate", "tonne", "phosphate_fertilizer", "ag_inputs", "PPI_C26"),
    ProductSeed("mop_62_white_port", "钾肥", "Potassium Fertilizer", "62% white muriate of potash, port price", "tonne", "potash_fertilizer", "ag_inputs", "PPI_C26"),
]

FLOAT_GLASS_2026 = ProductSeed(
    "float_glass_5_6mm", "浮法平板玻璃", "Float Flat Glass", "5/6mm", "tonne",
    "float_glass", "nonmetallic", "PPI_C30"
)

PRODUCTS_2026 = [
    product for product in PRODUCTS_2025
    if product.slug not in REMOVED_2026 and product.slug != "float_glass_4_8_5mm"
] + ADDED_2026 + [FLOAT_GLASS_2026]

assert len(PRODUCTS_2025) == 50
assert len(PRODUCTS_2026) == 50
