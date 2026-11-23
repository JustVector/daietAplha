# Warianty po obróbce termicznej – pokrycie

Wygenerowane przez `make cooked-variants` (S-106) z `data-pipeline/mapping/mapping.csv`, `data-pipeline/cooking/` i tabeli retencji USDA R6 – nie edytuj ręcznie. Logika przeliczenia: [cooking_calc.md](cooking_calc.md).

## Podsumowanie

| Warianty produktów | Liczba |
| --- | --- |
| na liście | 636 |
| z wartościami zmierzonymi (`measured`, rekord USDA) | 482 |
| obróbki termicznej bez rekordu USDA | 122 |
| wyliczone (`calculated`) | 82 |
| bez wartości | 40 |

| Źródło wydajności | Wyliczone warianty |
| --- | --- |
| `bognar_2002` | 39 |
| `usda_meat_yields_2012` | 15 |
| `usda_sr_pairs` | 28 |

## Wyliczone warianty (82)

Y – wydajność (masa po obróbce w % masy produktu wyjściowego); olej – gramy oleju wchłoniętego na 100 g produktu wyjściowego.

| variant_id | Produkt | Wariant | Baza (variant_id, fdc_id) | Proces R6 | Y % | Źródło Y | Olej g |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | ziemniak | smażony | surowy (1, 170026) | 3315 POTATOES,FRIED | 90.2 | vegetables: mediana 5 par USDA (cebula, kiełki fasoli mung, papryka czerwona, papryka zielona, pieczarka) | 11.21 |
| 12 | marchew | duszony | surowy (9, 170393) | 3456 VEG,ROOTS,ETC,BOILED,WATER USED | 102 | root_vegetables: tab. 17: Root and tuber vegetables, stewed, FR/TK m.S | – |
| 29 | por | duszony | surowy (27, 169246) | 3776 VEG,OTHER,BLD,WATER USED | 89 | allium_vegetables: tab. 17: Leek, stew, FR m.Z | – |
| 32 | cebula | duszony | surowy (30, 170000) | 3776 VEG,OTHER,BLD,WATER USED | 89 | allium_vegetables: tab. 17: Leek, stew, FR m.Z | – |
| 38 | czosnek | smażony | surowy (37, 169230) | 3780 VEG,OTHER,FRIED | 90.2 | vegetables: mediana 5 par USDA (cebula, kiełki fasoli mung, papryka czerwona, papryka zielona, pieczarka) | 11.21 |
| 44 | kapusta biała | duszony | surowy (42, 169975) | 3776 VEG,OTHER,BLD,WATER USED | 93 | brassicas: tab. 18: White cabbage, stewed, FR o.Z | – |
| 47 | kapusta czerwona | duszony | surowy (45, 169977) | 3776 VEG,OTHER,BLD,WATER USED | 93 | brassicas: tab. 18: White cabbage, stewed, FR o.Z | – |
| 53 | kapusta kiszona | duszony | gotowy (52, 169279) | 3776 VEG,OTHER,BLD,WATER USED | 92 | vegetable_preserves: tab. 18: Sauerkraut, boiled, FR/VK o.Z (brak duszenia bez dodatków) | – |
| 72 | szpinak | duszony | surowy (70, 168462) | 3006 VEG,GREENS,BOILED,WATER USED | 94 | leafy_vegetables: tab. 18: Leafy vegetables, stewed, FR/TK o.Z | – |
| 91 | papryka czerwona | duszony | surowy (90, 170108) | 3776 VEG,OTHER,BLD,WATER USED | 76 | nightshade_vegetables: tab. 19: Fruit vegetables, stew, FR m.Z | – |
| 102 | cukinia | duszony | surowy (100, 169291) | 3776 VEG,OTHER,BLD,WATER USED | 73 | cucurbit_vegetables: tab. 19: Zucchini, stew, FR m.Z | – |
| 104 | cukinia | smażony | surowy (100, 169291) | 3780 VEG,OTHER,FRIED | 90.2 | vegetables: mediana 5 par USDA (cebula, kiełki fasoli mung, papryka czerwona, papryka zielona, pieczarka) | 11.21 |
| 108 | bakłażan | smażony | surowy (106, 169228) | 3780 VEG,OTHER,FRIED | 90.2 | vegetables: mediana 5 par USDA (cebula, kiełki fasoli mung, papryka czerwona, papryka zielona, pieczarka) | 11.21 |
| 136 | pak choi | smażony | surowy (134, 170390) | 3780 VEG,OTHER,FRIED | 90.2 | vegetables: mediana 5 par USDA (cebula, kiełki fasoli mung, papryka czerwona, papryka zielona, pieczarka) | 11.21 |
| 149 | pieczarka | duszony | surowy (148, 169251) | 3776 VEG,OTHER,BLD,WATER USED | 82 | mushrooms: tab. 24: Mushroom, stew, FR m.Z | – |
| 153 | boczniak | smażony | surowy (152, 168580) | 3780 VEG,OTHER,FRIED | 90.2 | vegetables: mediana 5 par USDA (cebula, kiełki fasoli mung, papryka czerwona, papryka zielona, pieczarka) | 11.21 |
| 158 | kurka | duszony | surowy (157, 168422) | 3776 VEG,OTHER,BLD,WATER USED | 82 | mushrooms: tab. 24: Mushroom, stew, FR m.Z | – |
| 159 | kurka | smażony | surowy (157, 168422) | 3780 VEG,OTHER,FRIED | 90.2 | vegetables: mediana 5 par USDA (cebula, kiełki fasoli mung, papryka czerwona, papryka zielona, pieczarka) | 11.21 |
| 215 | kasza gryczana niepalona (biała) | gotowany | surowy (214, 170286) | 432 RICE,WHITE/BROWN,COOKED,WATER USED | 360 | food:125: tab. 29: Buckwheat (shacked corn), boiled | – |
| 255 | płatki owsiane | gotowany | surowy (254, 173904) | 352 OATMEAL,REG/QUICK,COOKED | 410 | flakes_bran: tab. 29: Oats flakes, wholemeal, boiled, TR o.Z | – |
| 324 | białko jaja kurzego | gotowany | surowy (323, 172183) | 105 EGGS,HARD COOKED | 101 | egg_products: tab. 2: Egg, boiled – masa po ugotowaniu 1,01 masy surowej (z waste) | – |
| 326 | żółtko jaja kurzego | gotowany | surowy (325, 172184) | 105 EGGS,HARD COOKED | 101 | egg_products: tab. 2: Egg, boiled – masa po ugotowaniu 1,01 masy surowej (z waste) | – |
| 328 | jajo przepiórcze | gotowany | surowy (327, 172191) | 105 EGGS,HARD COOKED | 101 | egg_products: tab. 2: Egg, boiled – masa po ugotowaniu 1,01 masy surowej (z waste) | – |
| 334 | pierś z kurczaka | grillowany | surowy (329, 171509) | 801 CHICKEN,BROILED | 78.6 | meat: mediana 5 par USDA (karkówka, polędwica wołowa, polędwiczka wieprzowa, rostbef, schab) | – |
| 340 | udo z kurczaka | grillowany | surowy (335, 173627) | 801 CHICKEN,BROILED | 78.6 | meat: mediana 5 par USDA (karkówka, polędwica wołowa, polędwiczka wieprzowa, rostbef, schab) | – |
| 345 | podudzie z kurczaka | grillowany | surowy (341, 173614) | 801 CHICKEN,BROILED | 78.6 | meat: mediana 5 par USDA (karkówka, polędwica wołowa, polędwiczka wieprzowa, rostbef, schab) | – |
| 349 | skrzydełko z kurczaka | grillowany | surowy (346, 172390) | 801 CHICKEN,BROILED | 78.6 | meat: mediana 5 par USDA (karkówka, polędwica wołowa, polędwiczka wieprzowa, rostbef, schab) | – |
| 362 | mięso mielone z kurczaka | duszony | surowy (361, 171116) | 851 CHICKEN,BROWN,SIMMER,WO/DRIPPINGS | 67 | meat: mediana 15 par USDA (cielęcina (udziec), karkówka, królik, mostek wołowy, pierś z kurczaka, pręga wołowa, schab, serca drobiowe, udo z kurczaka, wątróbka drobiowa, wątróbka wieprzowa, łopatka wieprzowa, łopatka wołowa, żeberka wieprzowe, żołądki drobiowe) | – |
| 365 | pierś z indyka | duszony | surowy (364, 171098) | 851 CHICKEN,BROWN,SIMMER,WO/DRIPPINGS | 67 | meat: mediana 15 par USDA (cielęcina (udziec), karkówka, królik, mostek wołowy, pierś z kurczaka, pręga wołowa, schab, serca drobiowe, udo z kurczaka, wątróbka drobiowa, wątróbka wieprzowa, łopatka wieprzowa, łopatka wołowa, żeberka wieprzowe, żołądki drobiowe) | – |
| 367 | pierś z indyka | smażony | surowy (364, 171098) | 803 CHICKEN,FRIED,WO/COATING | 64.7 | poultry: mediana 5 par USDA (mięso mielone z kurczaka, pierś z kurczaka, podudzie z kurczaka, skrzydełko z kurczaka, udo z kurczaka) | 0.77 |
| 368 | pierś z indyka | grillowany | surowy (364, 171098) | 801 CHICKEN,BROILED | 78.6 | meat: mediana 5 par USDA (karkówka, polędwica wołowa, polędwiczka wieprzowa, rostbef, schab) | – |
| 370 | udziec z indyka | duszony | surowy (369, 171090) | 851 CHICKEN,BROWN,SIMMER,WO/DRIPPINGS | 67 | meat: mediana 15 par USDA (cielęcina (udziec), karkówka, królik, mostek wołowy, pierś z kurczaka, pręga wołowa, schab, serca drobiowe, udo z kurczaka, wątróbka drobiowa, wątróbka wieprzowa, łopatka wieprzowa, łopatka wołowa, żeberka wieprzowe, żołądki drobiowe) | – |
| 373 | mięso mielone z indyka | duszony | surowy (372, 171505) | 851 CHICKEN,BROWN,SIMMER,WO/DRIPPINGS | 67 | meat: mediana 15 par USDA (cielęcina (udziec), karkówka, królik, mostek wołowy, pierś z kurczaka, pręga wołowa, schab, serca drobiowe, udo z kurczaka, wątróbka drobiowa, wątróbka wieprzowa, łopatka wieprzowa, łopatka wołowa, żeberka wieprzowe, żołądki drobiowe) | – |
| 374 | mięso mielone z indyka | smażony | surowy (372, 171505) | 803 CHICKEN,FRIED,WO/COATING | 64.7 | poultry: mediana 5 par USDA (mięso mielone z kurczaka, pierś z kurczaka, podudzie z kurczaka, skrzydełko z kurczaka, udo z kurczaka) | 0.77 |
| 386 | polędwiczka wieprzowa | smażony | surowy (384, 168249) | 1252 PORK,FRESH,FRIED,WO/COATING | 77 | pork: mediana 11 rekordów Pork, fresh – Pan-fried, Pan-broiled, Pan-browned (tabela danych, s. 29–45 PDF) | 0.55 |
| 393 | łopatka wieprzowa | gotowany | surowy (392, 168255) | 1301 PORK,FRESH,ROAST,SIMMERED WO/DRIP | 74.6 | meat: mediana 7 par USDA (kurczak (tuszka), parówki, pierś z kurczaka, podudzie z kurczaka, pręga wołowa, udo z kurczaka, żołądki drobiowe) | – |
| 397 | szynka wieprzowa surowa | gotowany | surowy (396, 168224) | 1301 PORK,FRESH,ROAST,SIMMERED WO/DRIP | 74.6 | meat: mediana 7 par USDA (kurczak (tuszka), parówki, pierś z kurczaka, podudzie z kurczaka, pręga wołowa, udo z kurczaka, żołądki drobiowe) | – |
| 398 | szynka wieprzowa surowa | duszony | surowy (396, 168224) | 1351 PORK,FRSH,CHOPS,BRWN,SIMMRD,WO/DRIP | 74 | pork: mediana 18 rekordów Pork, fresh – Braised (tabela danych, s. 29–45 PDF) | – |
| 401 | boczek surowy | pieczony | surowy (400, 167812) | 1254 PORK,FRESH,ROASTED | 77 | pork: mediana 18 rekordów Pork, fresh – Baked or Roasted (tabela danych, s. 29–45 PDF) | – |
| 402 | boczek surowy | smażony | surowy (400, 167812) | 1252 PORK,FRESH,FRIED,WO/COATING | 77 | pork: mediana 11 rekordów Pork, fresh – Pan-fried, Pan-broiled, Pan-browned (tabela danych, s. 29–45 PDF) | 0.55 |
| 406 | żeberka wieprzowe | grillowany | surowy (403, 167853) | 1251 PORK,FRESH,BROILED | 80.5 | pork: mediana 16 rekordów Pork, fresh – Broiled or Grilled (tabela danych, s. 29–45 PDF) | – |
| 408 | golonka | gotowany | surowy (407, 169157) | 1301 PORK,FRESH,ROAST,SIMMERED WO/DRIP | 74.6 | meat: mediana 7 par USDA (kurczak (tuszka), parówki, pierś z kurczaka, podudzie z kurczaka, pręga wołowa, udo z kurczaka, żołądki drobiowe) | – |
| 409 | golonka | pieczony | surowy (407, 169157) | 1254 PORK,FRESH,ROASTED | 77 | pork: mediana 18 rekordów Pork, fresh – Baked or Roasted (tabela danych, s. 29–45 PDF) | – |
| 411 | mięso mielone wieprzowe | duszony | surowy (410, 167902) | 1351 PORK,FRSH,CHOPS,BRWN,SIMMRD,WO/DRIP | 74 | pork: mediana 18 rekordów Pork, fresh – Braised (tabela danych, s. 29–45 PDF) | – |
| 412 | mięso mielone wieprzowe | smażony | surowy (410, 167902) | 1252 PORK,FRESH,FRIED,WO/COATING | 77 | pork: mediana 11 rekordów Pork, fresh – Pan-fried, Pan-broiled, Pan-browned (tabela danych, s. 29–45 PDF) | 0.55 |
| 415 | wątróbka wieprzowa | smażony | surowy (413, 167862) | 1151 LIVER,FRIED | 65.2 | meat: mediana 10 par USDA (cielęcina (udziec), mięso mielone wołowe, mięso mielone z kurczaka, pierś z kurczaka, podudzie z kurczaka, schab, skrzydełko z kurczaka, udo z kurczaka, wątróbka drobiowa, wątróbka wołowa) | 0.55 |
| 417 | polędwica wołowa | pieczony | surowy (416, 171803) | 601 BEEF,ROASTED | 80 | beef_veal: mediana 17 rekordów Beef/Veal – Baked or Roasted (tabela danych, s. 29–45 PDF) | – |
| 418 | polędwica wołowa | smażony | surowy (416, 171803) | 604 BEEF,FRIED,W/O COATING | 73 | beef_veal: mediana 3 rekordów Beef/Veal – Pan-fried, Pan-browned (tabela danych, s. 29–45 PDF) | 0.55 |
| 421 | rostbef | pieczony | surowy (420, 173116) | 601 BEEF,ROASTED | 80 | beef_veal: mediana 17 rekordów Beef/Veal – Baked or Roasted (tabela danych, s. 29–45 PDF) | – |
| 422 | rostbef | smażony | surowy (420, 173116) | 604 BEEF,FRIED,W/O COATING | 73 | beef_veal: mediana 3 rekordów Beef/Veal – Pan-fried, Pan-browned (tabela danych, s. 29–45 PDF) | 0.55 |
| 425 | antrykot | smażony | surowy (424, 171735) | 604 BEEF,FRIED,W/O COATING | 73 | beef_veal: mediana 3 rekordów Beef/Veal – Pan-fried, Pan-browned (tabela danych, s. 29–45 PDF) | 0.55 |
| 426 | antrykot | grillowany | surowy (424, 171735) | 602 BEEF,BROILED CUT | 77 | beef_veal: mediana 45 rekordów Beef/Veal – Broiled or Grilled (tabela danych, s. 29–45 PDF) | – |
| 428 | łopatka wołowa | gotowany | surowy (427, 174056) | 653 BEEF,ROAST,SIMMERED,WO/DRIPPINGS | 74.6 | meat: mediana 7 par USDA (kurczak (tuszka), parówki, pierś z kurczaka, podudzie z kurczaka, pręga wołowa, udo z kurczaka, żołądki drobiowe) | – |
| 434 | mostek wołowy | gotowany | surowy (433, 174057) | 653 BEEF,ROAST,SIMMERED,WO/DRIPPINGS | 74.6 | meat: mediana 7 par USDA (kurczak (tuszka), parówki, pierś z kurczaka, podudzie z kurczaka, pręga wołowa, udo z kurczaka, żołądki drobiowe) | – |
| 437 | mięso mielone wołowe | duszony | surowy (436, 174036) | 751 BEEF,GROUND,BRWN,SIMMER,WO/DRIPPING | 68 | beef_veal: mediana 19 rekordów Beef/Veal – Braised (tabela danych, s. 29–45 PDF) | – |
| 446 | jagnięcina (udziec) | duszony | surowy (445, 174313) | 1051 LAMB,BROWN,SIMMER,WO/DRIPPINGS | 67 | meat: mediana 15 par USDA (cielęcina (udziec), karkówka, królik, mostek wołowy, pierś z kurczaka, pręga wołowa, schab, serca drobiowe, udo z kurczaka, wątróbka drobiowa, wątróbka wieprzowa, łopatka wieprzowa, łopatka wołowa, żeberka wieprzowe, żołądki drobiowe) | – |
| 448 | jagnięcina (udziec) | grillowany | surowy (445, 174313) | 1001 LAMB, BROILED | 78.6 | meat: mediana 5 par USDA (karkówka, polędwica wołowa, polędwiczka wieprzowa, rostbef, schab) | – |
| 459 | kiełbasa śląska | smażony | gotowy (458, 174577) | 1659 SAUSAGE,RTE,FRANKS,ETC,SAUTEED | 90 | sausages: tab. 12: Meat loaf in slices, pan fried, FR o.Z (bez dodatku tłuszczu) | – |
| 460 | kiełbasa śląska | grillowany | gotowy (458, 174577) | 1657 SAUSAGE,RTE,FRANKS,ETC,BROILED | 84 | sausages: tab. 12: Meat loaf in slices, fried in oven, FR o.Z – przyjęte dla grillowania | – |
| 462 | kiełbasa wieprzowa wędzona | pieczony | gotowy (461, 174584) | 1657 SAUSAGE,RTE,FRANKS,ETC,BROILED | 84 | sausages: tab. 12: Meat loaf in slices, fried in oven, FR o.Z | – |
| 463 | kiełbasa wieprzowa wędzona | smażony | gotowy (461, 174584) | 1659 SAUSAGE,RTE,FRANKS,ETC,SAUTEED | 90 | sausages: tab. 12: Meat loaf in slices, pan fried, FR o.Z (bez dodatku tłuszczu) | – |
| 464 | kiełbasa wieprzowa wędzona | grillowany | gotowy (461, 174584) | 1657 SAUSAGE,RTE,FRANKS,ETC,BROILED | 84 | sausages: tab. 12: Meat loaf in slices, fried in oven, FR o.Z – przyjęte dla grillowania | – |
| 478 | kaszanka | pieczony | gotowy (477, 171618) | 1657 SAUSAGE,RTE,FRANKS,ETC,BROILED | 84 | offal_products: tab. 12: Meat loaf in slices, fried in oven, FR o.Z | – |
| 479 | kaszanka | smażony | gotowy (477, 171618) | 1659 SAUSAGE,RTE,FRANKS,ETC,SAUTEED | 90 | offal_products: tab. 12: Meat loaf in slices, pan fried, FR o.Z (bez dodatku tłuszczu) | – |
| 480 | kaszanka | grillowany | gotowy (477, 171618) | 1657 SAUSAGE,RTE,FRANKS,ETC,BROILED | 84 | offal_products: tab. 12: Meat loaf in slices, fried in oven, FR o.Z – przyjęte dla grillowania | – |
| 483 | łosoś | gotowany na parze | surowy (482, 175167) | 2551 FINFISH,>5%FAT,SIMMERED,WO/DRIP | 80 | sea_fish: tab. 13: Fish, fillet (cod, pollack), steamed | – |
| 485 | łosoś | smażony | surowy (482, 175167) | 2459 FINFISH,>5%FAT,FRIED,WO/COATING | 80 | sea_fish: tab. 13: Fish, fillet (cod, red fish, pollack), fried | 1.7 |
| 489 | dorsz | gotowany | surowy (488, 171955) | 2401 FINFISH,<5%FAT,SIMMERED,WO/DRIPPING | 77 | sea_fish: tab. 13: Fish, fillet (cod, red fish, pollack), boiled | – |
| 490 | dorsz | gotowany na parze | surowy (488, 171955) | 2401 FINFISH,<5%FAT,SIMMERED,WO/DRIPPING | 80 | sea_fish: tab. 13: Fish, fillet (cod, pollack), steamed | – |
| 492 | dorsz | smażony | surowy (488, 171955) | 2309 FINFISH,<5%FAT,FRIED,WO/COATING | 80 | sea_fish: tab. 13: Fish, fillet (cod, red fish, pollack), fried | 1.7 |
| 495 | mintaj | smażony | surowy (493, 173725) | 2309 FINFISH,<5%FAT,FRIED,WO/COATING | 80 | sea_fish: tab. 13: Fish, fillet (cod, red fish, pollack), fried | 1.7 |
| 501 | tilapia | smażony | surowy (499, 175176) | 2309 FINFISH,<5%FAT,FRIED,WO/COATING | 80 | freshwater_fish: tab. 13: Fish, fillet (cod, red fish, pollack), fried | 1.7 |
| 504 | panga | smażony | surowy (502, 175165) | 2459 FINFISH,>5%FAT,FRIED,WO/COATING | 80 | freshwater_fish: tab. 13: Fish, fillet (cod, red fish, pollack), fried | 1.7 |
| 507 | pstrąg | smażony | surowy (505, 173717) | 2459 FINFISH,>5%FAT,FRIED,WO/COATING | 80 | freshwater_fish: tab. 13: Fish, fillet (cod, red fish, pollack), fried | 1.7 |
| 512 | karp | smażony | surowy (510, 171952) | 2459 FINFISH,>5%FAT,FRIED,WO/COATING | 80 | freshwater_fish: tab. 13: Fish, fillet (cod, red fish, pollack), fried | 1.7 |
| 517 | sandacz | smażony | surowy (515, 175128) | 2309 FINFISH,<5%FAT,FRIED,WO/COATING | 80 | freshwater_fish: tab. 13: Fish, fillet (cod, red fish, pollack), fried | 1.7 |
| 519 | okoń | smażony | surowy (518, 173678) | 2309 FINFISH,<5%FAT,FRIED,WO/COATING | 80 | freshwater_fish: tab. 13: Fish, fillet (cod, red fish, pollack), fried | 1.7 |
| 524 | sola | smażony | surowy (522, 174196) | 2309 FINFISH,<5%FAT,FRIED,WO/COATING | 80 | sea_fish: tab. 13: Fish, fillet (cod, red fish, pollack), fried | 1.7 |
| 526 | tuńczyk świeży | smażony | surowy (525, 175159) | 2309 FINFISH,<5%FAT,FRIED,WO/COATING | 80 | sea_fish: tab. 13: Fish, fillet (cod, red fish, pollack), fried | 1.7 |
| 534 | śledź | smażony | surowy (532, 175116) | 2459 FINFISH,>5%FAT,FRIED,WO/COATING | 80 | sea_fish: tab. 13: Fish, fillet (cod, red fish, pollack), fried | 1.7 |
| 548 | krewetki | grillowany | surowy (545, 175179) | 2753 SHELLFISH,WO/SHELL,BROILED | 83.7 | fish_seafood: mediana 4 par USDA (makrela, pstrąg, tuńczyk świeży, łosoś) | – |
| 567 | soczewica czerwona | gotowany | surowy (566, 174284) | 501 LEGUMES,CKD 15/20MIN,BOILED,DRAINED | 279 | dry_legumes: mediana 8 par USDA (ciecierzyca, fasola biała, fasola czarna, fasola czerwona, fasola mung, groch łuskany, soczewica zielona, soja (nasiona)) | – |

## Warianty bez wartości (40)

Do uzupełnienia z drugiego źródła (Ciqual, Fineli) albo po weryfikacji mapowania (S-104).

| variant_id | Produkt | Wariant | Powód |
| --- | --- | --- | --- |
| 13 | marchew | pieczony | brak wydajności dla wariantu obróbki w grupie produktu |
| 16 | burak ćwikłowy | pieczony | brak wydajności dla wariantu obróbki w grupie produktu |
| 18 | pietruszka (korzeń) | gotowany | brak wariantu bazowego w USDA |
| 21 | seler korzeniowy | pieczony | brak wydajności dla wariantu obróbki w grupie produktu |
| 26 | pasternak | pieczony | brak wydajności dla wariantu obróbki w grupie produktu |
| 33 | cebula | pieczony | brak wydajności dla wariantu obróbki w grupie produktu |
| 57 | brukselka | pieczony | brak wydajności dla wariantu obróbki w grupie produktu |
| 61 | kalafior | pieczony | brak wydajności dla wariantu obróbki w grupie produktu |
| 65 | brokuł | pieczony | brak wydajności dla wariantu obróbki w grupie produktu |
| 84 | pomidor | pieczony | brak wydajności dla wariantu obróbki w grupie produktu |
| 92 | papryka czerwona | pieczony | brak wydajności dla wariantu obróbki w grupie produktu |
| 94 | papryka czerwona | grillowany | brak wydajności dla wariantu obróbki w grupie produktu |
| 98 | papryka żółta | pieczony | brak wydajności dla wariantu obróbki w grupie produktu |
| 103 | cukinia | pieczony | brak wydajności dla wariantu obróbki w grupie produktu |
| 105 | cukinia | grillowany | brak wydajności dla wariantu obróbki w grupie produktu |
| 107 | bakłażan | pieczony | brak wydajności dla wariantu obróbki w grupie produktu |
| 109 | bakłażan | grillowany | brak wydajności dla wariantu obróbki w grupie produktu |
| 112 | dynia | pieczony | brak wydajności dla wariantu obróbki w grupie produktu |
| 126 | kukurydza cukrowa (kolba) | grillowany | brak wydajności dla wariantu obróbki w grupie produktu |
| 131 | szparagi | grillowany | brak wydajności dla wariantu obróbki w grupie produktu |
| 133 | koper włoski (fenkuł) | pieczony | brak wydajności dla wariantu obróbki w grupie produktu |
| 144 | szczaw | gotowany | brak wariantu bazowego w USDA |
| 151 | pieczarka | grillowany | brak wydajności dla wariantu obróbki w grupie produktu |
| 155 | borowik (prawdziwek) | duszony | brak wariantu bazowego w USDA |
| 156 | borowik (prawdziwek) | smażony | brak wariantu bazowego w USDA |
| 162 | jabłko | pieczony | brak wydajności dla wariantu obróbki w grupie produktu |
| 315 | halloumi | smażony | brak wariantu bazowego w USDA |
| 316 | halloumi | grillowany | brak wariantu bazowego w USDA |
| 318 | oscypek | grillowany | brak wariantu bazowego w USDA |
| 467 | biała kiełbasa | pieczony | brak wariantu bazowego w USDA |
| 474 | boczek wędzony | smażony | brak danych (cold_cuts): brak źródła dla smażenia boczku i wędlin – bez wyliczenia (wydajność bardzo różna od mięsa) |
| 497 | morszczuk | pieczony | brak wariantu bazowego w USDA |
| 498 | morszczuk | smażony | brak wariantu bazowego w USDA |
| 542 | paluszki rybne | pieczony | brak wariantu bazowego w USDA |
| 543 | paluszki rybne | smażony | brak wariantu bazowego w USDA |
| 550 | kalmary | gotowany | brak wydajności dla wariantu obróbki w grupie produktu |
| 576 | edamame | gotowany | brak wariantu bazowego w USDA |
| 578 | tofu naturalne | pieczony | brak wydajności dla wariantu obróbki w grupie produktu |
| 580 | tofu naturalne | grillowany | brak wydajności dla wariantu obróbki w grupie produktu |
| 583 | tempeh | smażony | brak wydajności dla wariantu obróbki w grupie produktu |

## Pary USDA (wariant bazowy i po obróbce, oba zmierzone)

Wydajność z bilansu suchej masy bez tłuszczu; mediana grupy jest używana od co najmniej `min_pairs` par (methods.yaml), gdy `yields.csv` nie ma wpisu.

| Grupa | Wariant | Pary | Mediana Y % | Mediana tłuszczu g |
| --- | --- | --- | --- | --- |
| allium_vegetables | gotowany | 1 | 185.6 | 0.1 |
| allium_vegetables | smażony | 1 | 117.4 | 12.6 |
| beef_veal | duszony | 4 | 65.8 | 0.2 |
| beef_veal | gotowany | 1 | 65.3 | 0.3 |
| beef_veal | grillowany | 2 | 78.6 | -0.4 |
| beef_veal | pieczony | 1 | 75.7 | 0.8 |
| beef_veal | smażony | 2 | 59.9 | -3.5 |
| brassicas | gotowany | 10 | 104.6 | 0 |
| brassicas | gotowany na parze | 3 | 116.8 | 0.2 |
| cucurbit_vegetables | gotowany | 2 | 121.8 | 0 |
| dry_legumes | gotowany | 8 | 279 | 0 |
| egg_products | gotowany | 1 | 97.1 | 0.8 |
| egg_products | smażony | 1 | 91.4 | 4.1 |
| eggs | gotowany | 1 | 97.1 | 0.8 |
| eggs | smażony | 1 | 91.4 | 4.1 |
| fish_seafood | gotowany | 2 | 66.4 | -0.1 |
| fish_seafood | grillowany | 4 | 83.7 | 0 |
| fish_seafood | pieczony | 13 | 78 | 0 |
| fish_seafood | smażony | 2 | 66 | 5.4 |
| fresh_legume_vegetables | gotowany | 2 | 92.4 | -0.1 |
| fresh_legume_vegetables | gotowany na parze | 1 | 90.1 | 0 |
| fresh_legumes | gotowany | 1 | 116.5 | 0 |
| freshwater_fish | grillowany | 1 | 83.8 | 0 |
| freshwater_fish | pieczony | 6 | 78.2 | 0 |
| fruits | gotowany | 1 | 19.2 | -0.2 |
| grains | gotowany | 20 | 304.6 | 0.1 |
| groats_grains | gotowany | 11 | 333 | -0.2 |
| leafy_vegetables | gotowany | 2 | 89.6 | -0.1 |
| legume_products | smażony | 1 | 44 | 4.7 |
| legumes | gotowany | 9 | 267.8 | 0 |
| legumes | smażony | 1 | 44 | 4.7 |
| meat | duszony | 15 | 67 | -0.1 |
| meat | gotowany | 7 | 74.6 | -0.4 |
| meat | grillowany | 5 | 78.6 | 0.7 |
| meat | pieczony | 18 | 78.9 | 1.3 |
| meat | smażony | 10 | 65.2 | 0.6 |
| mushrooms | smażony | 1 | 84.1 | -0.1 |
| nightshade_vegetables | duszony | 1 | 31.6 | 0.6 |
| nightshade_vegetables | smażony | 2 | 99.1 | 11.9 |
| nuts | pieczony | 3 | 98.1 | 1.6 |
| nuts_seeds | pieczony | 6 | 93.6 | -3.6 |
| offal | duszony | 4 | 66.7 | -0.3 |
| offal | gotowany | 1 | 63.3 | -0.4 |
| offal | smażony | 2 | 71.4 | -0.3 |
| other_fruits | gotowany | 1 | 19.2 | -0.2 |
| other_meat | duszony | 1 | 66 | 0 |
| other_meat | pieczony | 2 | 72.2 | 0.7 |
| other_vegetables | gotowany | 3 | 90.1 | 0 |
| other_vegetables | gotowany na parze | 1 | 93.1 | 0.1 |
| other_vegetables | smażony | 1 | 60.8 | -0.1 |
| pasta | gotowany | 4 | 263.2 | 0.8 |
| pork | duszony | 4 | 71.1 | -1.1 |
| pork | grillowany | 3 | 70.6 | 0.7 |
| pork | pieczony | 6 | 80 | 1.9 |
| pork | smażony | 1 | 89.7 | 7.5 |
| poultry | duszony | 2 | 77.2 | 1.5 |
| poultry | gotowany | 4 | 77.2 | -0.1 |
| poultry | pieczony | 9 | 79.1 | 0.9 |
| poultry | smażony | 5 | 64.7 | 0.8 |
| rice | gotowany | 5 | 295.5 | 0.1 |
| root_vegetables | gotowany | 8 | 111.3 | 0 |
| root_vegetables | gotowany na parze | 2 | 105.5 | 0 |
| root_vegetables | pieczony | 2 | 67.7 | -0.2 |
| sausages | gotowany | 1 | 96.6 | -0.4 |
| sea_fish | grillowany | 3 | 83.7 | 0 |
| sea_fish | pieczony | 7 | 78 | 0 |
| seafood | gotowany | 2 | 66.4 | -0.1 |
| seafood | smażony | 2 | 66 | 5.4 |
| seeds | pieczony | 3 | 93.5 | -4.7 |
| vegetables | duszony | 1 | 31.6 | 0.6 |
| vegetables | gotowany | 28 | 103.9 | 0 |
| vegetables | gotowany na parze | 7 | 99.9 | 0 |
| vegetables | pieczony | 2 | 67.7 | -0.2 |
| vegetables | smażony | 5 | 90.2 | 11.2 |
