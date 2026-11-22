# Pokrycie składników odżywczych – USDA SR Legacy

> Plik generowany przez `make nutrient-coverage` (S-103) – nie edytuj ręcznie.

Dane: USDA FoodData Central – SR Legacy (2018-04): 7793 produktów, 149 składników z co najmniej jedną wartością (tabela szeroka, [S-102](../../backlog/S-102.md)).

**Pokrycie** składnika to odsetek produktów, które mają jego wartość. Brak wartości w źródle to `null`; zero podane przez USDA liczy się jako wartość.

Lista składników bazy v1: [`data-pipeline/nutrients.yaml`](../../data-pipeline/nutrients.yaml) (decyzje w [S-103](../../backlog/S-103.md)). Pokrycie liczone jest na całym SR Legacy; baza v1 obejmie 300–500 produktów podstawowych (S-101), więc ostateczne pokrycie będzie znane po mapowaniu (S-104).

## Składniki bazy v1 (38)

| # | Składnik | Jedn. | Kolumna USDA | id USDA | Produkty z wartością | Pokrycie |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Energia | kcal | `energy_kcal` | 1008 | 7793 | 100,0% |
| 2 | Białko | g | `protein_g` | 1003 | 7793 | 100,0% |
| 3 | Tłuszcz | g | `total_lipid_fat_g` | 1004 | 7793 | 100,0% |
| 4 | Węglowodany ogółem | g | `carbohydrate_by_difference_g` | 1005 | 7793 | 100,0% |
| 5 | Cukry | g | `sugars_total_g` | 2000 | 6007 | 77,1% |
| 6 | Błonnik pokarmowy | g | `fiber_total_dietary_g` | 1079 | 7231 | 92,8% |
| 7 | Woda | g | `water_g` | 1051 | 7793 | 100,0% |
| 8 | Kwasy tłuszczowe nasycone | g | `fatty_acids_total_saturated_g` | 1258 | 7450 | 95,6% |
| 9 | Kwasy tłuszczowe jednonienasycone | g | `fatty_acids_total_monounsaturated_g` | 1292 | 7277 | 93,4% |
| 10 | Kwasy tłuszczowe wielonienasycone | g | `fatty_acids_total_polyunsaturated_g` | 1293 | 7279 | 93,4% |
| 11 | Kwas linolenowy (18:3, głównie ALA) | g | `pufa_18_3_g` | 1270 | 6940 | 89,1% |
| 12 | Kwas eikozapentaenowy (EPA) | g | `pufa_20_5_n_3_epa_g` | 1278 | 5800 | 74,4% |
| 13 | Kwas dokozaheksaenowy (DHA) | g | `pufa_22_6_n_3_dha_g` | 1272 | 5772 | 74,1% |
| 14 | Kwasy tłuszczowe trans | g | `fatty_acids_total_trans_g` | 1257 | 4179 | 53,6% |
| 15 | Cholesterol | mg | `cholesterol_mg` | 1253 | 7394 | 94,9% |
| 16 | Sód | mg | `sodium_na_mg` | 1093 | 7709 | 98,9% |
| 17 | Potas | mg | `potassium_k_mg` | 1092 | 7516 | 96,4% |
| 18 | Wapń | mg | `calcium_ca_mg` | 1087 | 7708 | 98,9% |
| 19 | Magnez | mg | `magnesium_mg_mg` | 1090 | 7421 | 95,2% |
| 20 | Fosfor | mg | `phosphorus_p_mg` | 1091 | 7467 | 95,8% |
| 21 | Żelazo | mg | `iron_fe_mg` | 1089 | 7713 | 99,0% |
| 22 | Cynk | mg | `zinc_zn_mg` | 1095 | 7406 | 95,0% |
| 23 | Miedź | mg | `copper_cu_mg` | 1098 | 7284 | 93,5% |
| 24 | Mangan | mg | `manganese_mn_mg` | 1101 | 6492 | 83,3% |
| 25 | Selen | µg | `selenium_se_ug` | 1103 | 6865 | 88,1% |
| 26 | Witamina A (RAE) | µg | `vitamin_a_rae_ug` | 1106 | 6918 | 88,8% |
| 27 | Witamina D (D2 + D3) | µg | `vitamin_d_d2_d3_ug` | 1114 | 5185 | 66,5% |
| 28 | Witamina E (alfa-tokoferol) | mg | `vitamin_e_alpha_tocopherol_mg` | 1109 | 5580 | 71,6% |
| 29 | Witamina K (filochinon) | µg | `vitamin_k_phylloquinone_ug` | 1185 | 5054 | 64,9% |
| 30 | Witamina C | mg | `vitamin_c_total_ascorbic_acid_mg` | 1162 | 7332 | 94,1% |
| 31 | Tiamina (witamina B1) | mg | `thiamin_mg` | 1165 | 7402 | 95,0% |
| 32 | Ryboflawina (witamina B2) | mg | `riboflavin_mg` | 1166 | 7421 | 95,2% |
| 33 | Niacyna (witamina B3) | mg | `niacin_mg` | 1167 | 7402 | 95,0% |
| 34 | Witamina B6 | mg | `vitamin_b_6_mg` | 1175 | 7262 | 93,2% |
| 35 | Foliany (DFE) | µg | `folate_dfe_ug` | 1190 | 6482 | 83,2% |
| 36 | Witamina B12 | µg | `vitamin_b_12_ug` | 1178 | 7113 | 91,3% |
| 37 | Alkohol etylowy | g | `alcohol_ethyl_g` | 1018 | 5399 | 69,3% |
| 38 | Kofeina | mg | `caffeine_mg` | 1057 | 5215 | 66,9% |

## Pokrycie składników v1 według kategorii USDA

Średnie pokrycie = średnia z pokrycia wszystkich składników v1 w kategorii. Ostatnia kolumna wymienia składniki v1 z pokryciem poniżej 50,0% w danej kategorii.

| Kategoria USDA | Produkty | Średnie pokrycie | Pokrycie < 50,0% |
| --- | --- | --- | --- |
| American Indian/Alaska Native Foods | 165 | 58,2% | Kwas linolenowy (18:3, głównie ALA), Kwas eikozapentaenowy (EPA), Kwas dokozaheksaenowy (DHA), Kwasy tłuszczowe trans, Cholesterol, Selen, Witamina A (RAE), Witamina D (D2 + D3), Witamina E (alfa-tokoferol), Witamina K (filochinon), Foliany (DFE), Witamina B12, Alkohol etylowy, Kofeina |
| Baby Foods | 345 | 92,5% | Kwasy tłuszczowe trans, Mangan |
| Baked Products | 517 | 86,0% | Kwasy tłuszczowe trans |
| Beef Products | 954 | 94,0% | – |
| Beverages | 366 | 83,4% | – |
| Breakfast Cereals | 195 | 88,2% | Mangan |
| Cereal Grains and Pasta | 181 | 88,4% | Kwasy tłuszczowe trans |
| Dairy and Egg Products | 291 | 91,3% | Kwasy tłuszczowe trans |
| Fast Foods | 312 | 86,8% | Witamina D (D2 + D3), Foliany (DFE), Alkohol etylowy, Kofeina |
| Fats and Oils | 216 | 90,5% | Kwasy tłuszczowe trans, Mangan |
| Finfish and Shellfish Products | 264 | 88,0% | Cukry, Kwasy tłuszczowe trans, Witamina D (D2 + D3), Witamina E (alfa-tokoferol), Witamina K (filochinon), Kofeina |
| Fruits and Fruit Juices | 355 | 88,6% | – |
| Lamb, Veal, and Game Products | 464 | 83,5% | Cukry, Kwas eikozapentaenowy (EPA), Kwas dokozaheksaenowy (DHA), Kwasy tłuszczowe trans, Witamina D (D2 + D3), Witamina K (filochinon), Alkohol etylowy, Kofeina |
| Legumes and Legume Products | 290 | 83,6% | Kwas eikozapentaenowy (EPA), Kwas dokozaheksaenowy (DHA), Alkohol etylowy, Kofeina |
| Meals, Entrees, and Side Dishes | 81 | 94,1% | – |
| Nut and Seed Products | 137 | 85,8% | Kwasy tłuszczowe trans, Witamina K (filochinon), Kofeina |
| Pork Products | 336 | 95,1% | – |
| Poultry Products | 383 | 92,7% | Kwasy tłuszczowe trans |
| Restaurant Foods | 109 | 87,8% | Witamina D (D2 + D3), Witamina C, Foliany (DFE), Alkohol etylowy, Kofeina |
| Sausages and Luncheon Meats | 167 | 91,8% | Kwasy tłuszczowe trans |
| Snacks | 176 | 87,8% | Kwasy tłuszczowe trans |
| Soups, Sauces, and Gravies | 254 | 87,1% | Kwasy tłuszczowe trans |
| Spices and Herbs | 63 | 88,4% | – |
| Sweets | 358 | 83,0% | Kwasy tłuszczowe trans |
| Vegetables and Vegetable Products | 814 | 90,6% | – |

## Wszystkie składniki SR Legacy

Kolejność: `rank` z USDA (kolejność prezentacji w FoodData Central).

| Kolumna | id USDA | Nazwa USDA | Jedn. | Produkty z wartością | Pokrycie | Baza v1 |
| --- | --- | --- | --- | --- | --- | --- |
| `water_g` | 1051 | Water | g | 7793 | 100,0% | Woda |
| `energy_kcal` | 1008 | Energy | kcal | 7793 | 100,0% | Energia |
| `energy_kj` | 1062 | Energy | kJ | 7793 | 100,0% |  |
| `protein_g` | 1003 | Protein | g | 7793 | 100,0% | Białko |
| `total_lipid_fat_g` | 1004 | Total lipid (fat) | g | 7793 | 100,0% | Tłuszcz |
| `ash_g` | 1007 | Ash | g | 7790 | 100,0% |  |
| `carbohydrate_by_difference_g` | 1005 | Carbohydrate, by difference | g | 7793 | 100,0% | Węglowodany ogółem |
| `fiber_total_dietary_g` | 1079 | Fiber, total dietary | g | 7231 | 92,8% | Błonnik pokarmowy |
| `sugars_total_g` | 2000 | Sugars, Total | g | 6007 | 77,1% | Cukry |
| `sucrose_g` | 1010 | Sucrose | g | 1733 | 22,2% |  |
| `glucose_g` | 1011 | Glucose | g | 1740 | 22,3% |  |
| `fructose_g` | 1012 | Fructose | g | 1745 | 22,4% |  |
| `lactose_g` | 1013 | Lactose | g | 1712 | 22,0% |  |
| `maltose_g` | 1014 | Maltose | g | 1711 | 22,0% |  |
| `galactose_g` | 1075 | Galactose | g | 1579 | 20,3% |  |
| `starch_g` | 1009 | Starch | g | 1167 | 15,0% |  |
| `calcium_ca_mg` | 1087 | Calcium, Ca | mg | 7708 | 98,9% | Wapń |
| `iron_fe_mg` | 1089 | Iron, Fe | mg | 7713 | 99,0% | Żelazo |
| `magnesium_mg_mg` | 1090 | Magnesium, Mg | mg | 7421 | 95,2% | Magnez |
| `phosphorus_p_mg` | 1091 | Phosphorus, P | mg | 7467 | 95,8% | Fosfor |
| `potassium_k_mg` | 1092 | Potassium, K | mg | 7516 | 96,4% | Potas |
| `sodium_na_mg` | 1093 | Sodium, Na | mg | 7709 | 98,9% | Sód |
| `zinc_zn_mg` | 1095 | Zinc, Zn | mg | 7406 | 95,0% | Cynk |
| `copper_cu_mg` | 1098 | Copper, Cu | mg | 7284 | 93,5% | Miedź |
| `manganese_mn_mg` | 1101 | Manganese, Mn | mg | 6492 | 83,3% | Mangan |
| `selenium_se_ug` | 1103 | Selenium, Se | µg | 6865 | 88,1% | Selen |
| `fluoride_f_ug` | 1099 | Fluoride, F | µg | 538 | 6,9% |  |
| `vitamin_c_total_ascorbic_acid_mg` | 1162 | Vitamin C, total ascorbic acid | mg | 7332 | 94,1% | Witamina C |
| `thiamin_mg` | 1165 | Thiamin | mg | 7402 | 95,0% | Tiamina (witamina B1) |
| `riboflavin_mg` | 1166 | Riboflavin | mg | 7421 | 95,2% | Ryboflawina (witamina B2) |
| `niacin_mg` | 1167 | Niacin | mg | 7402 | 95,0% | Niacyna (witamina B3) |
| `pantothenic_acid_mg` | 1170 | Pantothenic acid | mg | 6376 | 81,8% |  |
| `vitamin_b_6_mg` | 1175 | Vitamin B-6 | mg | 7262 | 93,2% | Witamina B6 |
| `folate_total_ug` | 1177 | Folate, total | µg | 6851 | 87,9% |  |
| `folic_acid_ug` | 1186 | Folic acid | µg | 6500 | 83,4% |  |
| `folate_food_ug` | 1187 | Folate, food | µg | 6722 | 86,3% |  |
| `folate_dfe_ug` | 1190 | Folate, DFE | µg | 6482 | 83,2% | Foliany (DFE) |
| `choline_total_mg` | 1180 | Choline, total | mg | 4611 | 59,2% |  |
| `betaine_mg` | 1198 | Betaine | mg | 2091 | 26,8% |  |
| `vitamin_b_12_ug` | 1178 | Vitamin B-12 | µg | 7113 | 91,3% | Witamina B12 |
| `vitamin_b_12_added_ug` | 1246 | Vitamin B-12, added | µg | 4762 | 61,1% |  |
| `vitamin_a_rae_ug` | 1106 | Vitamin A, RAE | µg | 6918 | 88,8% | Witamina A (RAE) |
| `retinol_ug` | 1105 | Retinol | µg | 6788 | 87,1% |  |
| `carotene_beta_ug` | 1107 | Carotene, beta | µg | 5440 | 69,8% |  |
| `carotene_alpha_ug` | 1108 | Carotene, alpha | µg | 5352 | 68,7% |  |
| `cryptoxanthin_beta_ug` | 1120 | Cryptoxanthin, beta | µg | 5341 | 68,5% |  |
| `vitamin_a_iu_iu` | 1104 | Vitamin A, IU | IU | 7356 | 94,4% |  |
| `lycopene_ug` | 1122 | Lycopene | µg | 5314 | 68,2% |  |
| `lutein_zeaxanthin_ug` | 1123 | Lutein + zeaxanthin | µg | 5294 | 67,9% |  |
| `vitamin_e_alpha_tocopherol_mg` | 1109 | Vitamin E (alpha-tocopherol) | mg | 5580 | 71,6% | Witamina E (alfa-tokoferol) |
| `vitamin_e_added_mg` | 1242 | Vitamin E, added | mg | 4616 | 59,2% |  |
| `tocopherol_beta_mg` | 1125 | Tocopherol, beta | mg | 1890 | 24,3% |  |
| `tocopherol_gamma_mg` | 1126 | Tocopherol, gamma | mg | 1888 | 24,2% |  |
| `tocopherol_delta_mg` | 1127 | Tocopherol, delta | mg | 1872 | 24,0% |  |
| `tocotrienol_alpha_mg` | 1128 | Tocotrienol, alpha | mg | 1463 | 18,8% |  |
| `tocotrienol_beta_mg` | 1129 | Tocotrienol, beta | mg | 1477 | 19,0% |  |
| `tocotrienol_gamma_mg` | 1130 | Tocotrienol, gamma | mg | 1466 | 18,8% |  |
| `tocotrienol_delta_mg` | 1131 | Tocotrienol, delta | mg | 1461 | 18,7% |  |
| `vitamin_d_d2_d3_international_units_iu` | 1110 | Vitamin D (D2 + D3), International Units | IU | 5181 | 66,5% |  |
| `vitamin_d_d2_d3_ug` | 1114 | Vitamin D (D2 + D3) | µg | 5185 | 66,5% | Witamina D (D2 + D3) |
| `vitamin_d2_ergocalciferol_ug` | 1111 | Vitamin D2 (ergocalciferol) | µg | 138 | 1,8% |  |
| `vitamin_d3_cholecalciferol_ug` | 1112 | Vitamin D3 (cholecalciferol) | µg | 1819 | 23,3% |  |
| `vitamin_k_phylloquinone_ug` | 1185 | Vitamin K (phylloquinone) | µg | 5054 | 64,9% | Witamina K (filochinon) |
| `vitamin_k_dihydrophylloquinone_ug` | 1184 | Vitamin K (Dihydrophylloquinone) | µg | 1419 | 18,2% |  |
| `vitamin_k_menaquinone_4_ug` | 1183 | Vitamin K (Menaquinone-4) | µg | 606 | 7,8% |  |
| `fatty_acids_total_saturated_g` | 1258 | Fatty acids, total saturated | g | 7450 | 95,6% | Kwasy tłuszczowe nasycone |
| `sfa_4_0_g` | 1259 | SFA 4:0 | g | 5692 | 73,0% |  |
| `sfa_6_0_g` | 1260 | SFA 6:0 | g | 5729 | 73,5% |  |
| `sfa_8_0_g` | 1261 | SFA 8:0 | g | 5919 | 76,0% |  |
| `sfa_10_0_g` | 1262 | SFA 10:0 | g | 6268 | 80,4% |  |
| `sfa_12_0_g` | 1263 | SFA 12:0 | g | 6450 | 82,8% |  |
| `sfa_13_0_g` | 1332 | SFA 13:0 | g | 263 | 3,4% |  |
| `sfa_14_0_g` | 1264 | SFA 14:0 | g | 6793 | 87,2% |  |
| `sfa_15_0_g` | 1299 | SFA 15:0 | g | 2373 | 30,5% |  |
| `sfa_16_0_g` | 1265 | SFA 16:0 | g | 6999 | 89,8% |  |
| `sfa_17_0_g` | 1300 | SFA 17:0 | g | 2755 | 35,4% |  |
| `sfa_18_0_g` | 1266 | SFA 18:0 | g | 6989 | 89,7% |  |
| `sfa_20_0_g` | 1267 | SFA 20:0 | g | 2849 | 36,6% |  |
| `sfa_22_0_g` | 1273 | SFA 22:0 | g | 2316 | 29,7% |  |
| `sfa_24_0_g` | 1301 | SFA 24:0 | g | 2235 | 28,7% |  |
| `fatty_acids_total_monounsaturated_g` | 1292 | Fatty acids, total monounsaturated | g | 7277 | 93,4% | Kwasy tłuszczowe jednonienasycone |
| `mufa_14_1_g` | 1274 | MUFA 14:1 | g | 2725 | 35,0% |  |
| `mufa_15_1_g` | 1333 | MUFA 15:1 | g | 2076 | 26,6% |  |
| `mufa_16_1_g` | 1275 | MUFA 16:1 | g | 6782 | 87,0% |  |
| `mufa_16_1_c_g` | 1314 | MUFA 16:1 c | g | 1382 | 17,7% |  |
| `mufa_17_1_g` | 1323 | MUFA 17:1 | g | 2459 | 31,6% |  |
| `mufa_18_1_g` | 1268 | MUFA 18:1 | g | 7015 | 90,0% |  |
| `mufa_18_1_c_g` | 1315 | MUFA 18:1 c | g | 1864 | 23,9% |  |
| `mufa_18_1_11_t_18_1t_n_7_g` | 1412 | MUFA 18:1-11 t (18:1t n-7) | g | 168 | 2,2% |  |
| `mufa_20_1_g` | 1277 | MUFA 20:1 | g | 6300 | 80,8% |  |
| `mufa_22_1_g` | 1279 | MUFA 22:1 | g | 5779 | 74,2% |  |
| `mufa_22_1_c_g` | 1317 | MUFA 22:1 c | g | 1164 | 14,9% |  |
| `mufa_24_1_c_g` | 1312 | MUFA 24:1 c | g | 1381 | 17,7% |  |
| `fatty_acids_total_polyunsaturated_g` | 1293 | Fatty acids, total polyunsaturated | g | 7279 | 93,4% | Kwasy tłuszczowe wielonienasycone |
| `pufa_18_2_g` | 1269 | PUFA 18:2 | g | 7031 | 90,2% |  |
| `pufa_18_2_n_6_c_c_g` | 1316 | PUFA 18:2 n-6 c,c | g | 1842 | 23,6% |  |
| `pufa_18_2_clas_g` | 1311 | PUFA 18:2 CLAs | g | 1512 | 19,4% |  |
| `pufa_18_2_i_g` | 1307 | PUFA 18:2 i | g | 55 | 0,7% |  |
| `pufa_18_3_g` | 1270 | PUFA 18:3 | g | 6940 | 89,1% | Kwas linolenowy (18:3, głównie ALA) |
| `pufa_18_3_n_3_c_c_c_ala_g` | 1404 | PUFA 18:3 n-3 c,c,c (ALA) | g | 1967 | 25,2% |  |
| `pufa_18_3_n_6_c_c_c_g` | 1321 | PUFA 18:3 n-6 c,c,c | g | 1660 | 21,3% |  |
| `pufa_18_3i_g` | 1409 | PUFA 18:3i | g | 568 | 7,3% |  |
| `pufa_18_4_g` | 1276 | PUFA 18:4 | g | 5707 | 73,2% |  |
| `pufa_20_2_n_6_c_c_g` | 1313 | PUFA 20:2 n-6 c,c | g | 2487 | 31,9% |  |
| `pufa_20_3_g` | 1325 | PUFA 20:3 | g | 2284 | 29,3% |  |
| `pufa_20_3_n_3_g` | 1405 | PUFA 20:3 n-3 | g | 1035 | 13,3% |  |
| `pufa_20_4_n_6_g` | 1406 | PUFA 20:4 n-6 | g | 1260 | 16,2% |  |
| `pufa_20_4_g` | 1271 | PUFA 20:4 | g | 6304 | 80,9% |  |
| `pufa_2_4_n_6_g` | 1408 | PUFA 2:4 n-6 | g | 165 | 2,1% |  |
| `pufa_20_5_n_3_epa_g` | 1278 | PUFA 20:5 n-3 (EPA) | g | 5800 | 74,4% | Kwas eikozapentaenowy (EPA) |
| `pufa_21_5_g` | 1410 | PUFA 21:5 | g | 114 | 1,5% |  |
| `pufa_22_4_g` | 1411 | PUFA 22:4 | g | 1069 | 13,7% |  |
| `pufa_22_5_n_3_dpa_g` | 1280 | PUFA 22:5 n-3 (DPA) | g | 5756 | 73,9% |  |
| `pufa_22_6_n_3_dha_g` | 1272 | PUFA 22:6 n-3 (DHA) | g | 5772 | 74,1% | Kwas dokozaheksaenowy (DHA) |
| `fatty_acids_total_trans_g` | 1257 | Fatty acids, total trans | g | 4179 | 53,6% | Kwasy tłuszczowe trans |
| `fatty_acids_total_trans_monoenoic_g` | 1329 | Fatty acids, total trans-monoenoic | g | 1887 | 24,2% |  |
| `tfa_16_1_t_g` | 1303 | TFA 16:1 t | g | 1251 | 16,1% |  |
| `tfa_18_1_t_g` | 1304 | TFA 18:1 t | g | 1913 | 24,5% |  |
| `tfa_22_1_t_g` | 1305 | TFA 22:1 t | g | 878 | 11,3% |  |
| `tfa_18_2_t_not_further_defined_g` | 1306 | TFA 18:2 t not further defined | g | 1216 | 15,6% |  |
| `tfa_18_2_t_t_g` | 1310 | TFA 18:2 t,t | g | 352 | 4,5% |  |
| `fatty_acids_total_trans_polyenoic_g` | 1331 | Fatty acids, total trans-polyenoic | g | 1593 | 20,4% |  |
| `cholesterol_mg` | 1253 | Cholesterol | mg | 7394 | 94,9% | Cholesterol |
| `phytosterols_mg` | 1283 | Phytosterols | mg | 489 | 6,3% |  |
| `stigmasterol_mg` | 1285 | Stigmasterol | mg | 137 | 1,8% |  |
| `campesterol_mg` | 1286 | Campesterol | mg | 137 | 1,8% |  |
| `beta_sitosterol_mg` | 1288 | Beta-sitosterol | mg | 138 | 1,8% |  |
| `tryptophan_g` | 1210 | Tryptophan | g | 5030 | 64,5% |  |
| `threonine_g` | 1211 | Threonine | g | 5080 | 65,2% |  |
| `isoleucine_g` | 1212 | Isoleucine | g | 5084 | 65,2% |  |
| `leucine_g` | 1213 | Leucine | g | 5083 | 65,2% |  |
| `lysine_g` | 1214 | Lysine | g | 5097 | 65,4% |  |
| `methionine_g` | 1215 | Methionine | g | 5096 | 65,4% |  |
| `cystine_g` | 1216 | Cystine | g | 4930 | 63,3% |  |
| `phenylalanine_g` | 1217 | Phenylalanine | g | 5079 | 65,2% |  |
| `tyrosine_g` | 1218 | Tyrosine | g | 5049 | 64,8% |  |
| `valine_g` | 1219 | Valine | g | 5083 | 65,2% |  |
| `arginine_g` | 1220 | Arginine | g | 5070 | 65,1% |  |
| `histidine_g` | 1221 | Histidine | g | 5076 | 65,1% |  |
| `alanine_g` | 1222 | Alanine | g | 5025 | 64,5% |  |
| `aspartic_acid_g` | 1223 | Aspartic acid | g | 4872 | 62,5% |  |
| `glutamic_acid_g` | 1224 | Glutamic acid | g | 5029 | 64,5% |  |
| `glycine_g` | 1225 | Glycine | g | 5025 | 64,5% |  |
| `proline_g` | 1226 | Proline | g | 5017 | 64,4% |  |
| `serine_g` | 1227 | Serine | g | 5025 | 64,5% |  |
| `hydroxyproline_g` | 1228 | Hydroxyproline | g | 1431 | 18,4% |  |
| `alcohol_ethyl_g` | 1018 | Alcohol, ethyl | g | 5399 | 69,3% | Alkohol etylowy |
| `caffeine_mg` | 1057 | Caffeine | mg | 5215 | 66,9% | Kofeina |
| `theobromine_mg` | 1058 | Theobromine | mg | 5170 | 66,3% |  |
