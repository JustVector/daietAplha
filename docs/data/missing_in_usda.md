# Produkty bez odpowiednika w USDA SR Legacy

Wygenerowane przez `make map-products` (S-104) z `data-pipeline/mapping/mapping.csv` – nie edytuj ręcznie.

## Podsumowanie

| Status | Warianty |
| --- | --- |
| `auto` | 482 |
| `zweryfikowany` | 0 |
| `brak` | 154 |
| razem | 636 |

Status `brak` = najlepszy kandydat poniżej progu 85 (pozostali w `mapping_candidates.csv`); `zweryfikowany` z pustym `fdc_id` = brak potwierdzony ręcznie.

## Produkty do uzupełnienia z Ciqual lub Fineli (43 wariantów, 33 produktów)

Żaden wariant produktu nie ma odpowiednika w USDA – potrzebne drugie źródło ([ADR-0001](../adr/0001-food-database.md)).

| variant_id | Produkt | Wariant | Typowo polski | Status | Najlepszy kandydat USDA | Wynik | Uwagi z listy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 17 | pietruszka (korzeń) | surowy | tak | `brak` | Parsley, fresh | 68.7 | – |
| 18 | pietruszka (korzeń) | gotowany | tak | `brak` | Lotus root, cooked, boiled, drained, without salt | 47.3 | – |
| 34 | cebula czerwona | surowy | nie | `brak` | Onions, raw | 78.8 | – |
| 77 | roszponka | surowy | nie | `brak` | Lettuce, green leaf, raw | 7.6 | – |
| 143 | szczaw | surowy | tak | `brak` | Dock, raw | 54.2 | – |
| 144 | szczaw | gotowany | tak | `brak` | Dock, cooked, boiled, drained, without salt | 47.5 | – |
| 154 | borowik (prawdziwek) | surowy | tak | `brak` | Mushrooms, morel, raw | 52.1 | grzyb leśny |
| 155 | borowik (prawdziwek) | duszony | tak | `brak` | Mushrooms, shiitake, dried | 12.5 | grzyb leśny |
| 156 | borowik (prawdziwek) | smażony | tak | `brak` | Mushrooms, white, stir-fried | 45.8 | grzyb leśny |
| 160 | borowik suszony | gotowy | tak | `brak` | Mushrooms, shiitake, dried | 66.6 | grzyb leśny |
| 178 | aronia | surowy | tak | `brak` | Oheloberries, raw | 38.8 | – |
| 211 | sok z cytryny | gotowy | nie | `brak` | Lemon juice, raw | 70.0 | – |
| 259 | musli | gotowy | tak | `brak` | Cereals ready-to-eat, granola, homemade | 70.5 | w USDA tylko granola i batony |
| 260 | napój owsiany | gotowy | tak | `brak` | Beverages, Carob-flavor beverage mix, powder, prepared with whole milk | 52.7 | – |
| 286 | kefir | gotowy | tak | `brak` | Kefir, lowfat, plain, LIFEWAY | 73.1 | w USDA tylko produkt markowy |
| 288 | mleko zsiadłe | gotowy | tak | `brak` | Sour cream, imitation, cultured | 59.7 | – |
| 292 | skyr | gotowy | tak | `brak` | Yogurt, plain, skim milk | 44.0 | – |
| 293 | twaróg chudy | gotowy | tak | `brak` | Cheese, muenster, low fat | 62.6 | w USDA brak twarogu (serek wiejski to inny produkt) |
| 294 | twaróg półtłusty | gotowy | tak | `brak` | Cheese, cream, fat free | 34.4 | – |
| 295 | twaróg tłusty | gotowy | tak | `brak` | Cheese, muenster, low fat | 37.8 | – |
| 297 | serek homogenizowany naturalny | gotowy | tak | `brak` | Cheese, fresh, queso fresco | 40.2 | – |
| 312 | mascarpone | gotowy | tak | `brak` | Cheese, cream | 61.7 | – |
| 314 | halloumi | gotowy | tak | `brak` | Cheese, edam | 62.6 | – |
| 315 | halloumi | smażony | tak | `brak` | Cheese, edam | 37.6 | – |
| 316 | halloumi | grillowany | tak | `brak` | Cheese, edam | 37.6 | – |
| 317 | oscypek | gotowy | tak | `brak` | Cheese, ricotta, whole milk | 25.5 | – |
| 318 | oscypek | grillowany | tak | `brak` | Cheese, ricotta, whole milk | 0.5 | – |
| 319 | bryndza | gotowy | tak | `brak` | Cheese, ricotta, whole milk | 43.0 | – |
| 454 | polędwica sopocka | gotowy | tak | `brak` | Pork, cured, bacon, unprepared | 49.2 | – |
| 455 | szynka z indyka | gotowy | nie | `brak` | Ham, turkey, sliced, extra lean, prepackaged or deli | 74.6 | – |
| 496 | morszczuk | surowy | tak | `brak` | Fish, haddock, raw | 71.0 | w USDA brak morszczuka |
| 497 | morszczuk | pieczony | tak | `brak` | Fish, haddock, cooked, dry heat | 69.8 | w USDA brak morszczuka |
| 498 | morszczuk | smażony | tak | `brak` | Fish, catfish, channel, cooked, breaded and fried | 60.5 | w USDA brak morszczuka |
| 509 | pstrąg wędzony | gotowy | tak | `brak` | Fish, cisco, smoked | 65.5 | – |
| 531 | makrela wędzona | gotowy | tak | `brak` | Fish, mackerel, salted | 73.8 | – |
| 535 | śledź solony (matjas) | gotowy | tak | `brak` | Fish, herring, Pacific, cooked, dry heat | 66.7 | – |
| 537 | szprot wędzony | gotowy | tak | `brak` | Fish, cisco, smoked | 65.5 | – |
| 541 | makrela w sosie pomidorowym | gotowy | tak | `brak` | Fish, sardine, Pacific, canned in tomato sauce, drained solids with bone | 71.9 | – |
| 542 | paluszki rybne | pieczony | nie | `brak` | Fish, fish sticks, frozen, prepared | 60.3 | – |
| 543 | paluszki rybne | smażony | nie | `brak` | Fish, fish sticks, frozen, prepared | 60.3 | – |
| 544 | paluszki surimi | gotowy | nie | `brak` | Fish, surimi | 72.6 | – |
| 576 | edamame | gotowany | nie | `brak` | Edamame, frozen, prepared | 75.0 | – |
| 581 | tofu wędzone | gotowy | tak | `brak` | Tofu, hard, prepared with nigari | 47.8 | – |

## Brakujące warianty obróbki (111 wariantów, 79 produktów)

Produkt ma w USDA inny wariant obróbki – brakujący wariant do wyliczenia współczynnikami retencji i wydajności (S-106) albo z Ciqual lub Fineli.

| variant_id | Produkt | Wariant | Typowo polski | Status | Najlepszy kandydat USDA | Wynik | Uwagi z listy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | ziemniak | smażony | nie | `brak` | Potatoes, flesh and skin, raw | 45.0 | – |
| 12 | marchew | duszony | nie | `brak` | Carrots, canned, no salt added, drained solids | 61.7 | – |
| 13 | marchew | pieczony | nie | `brak` | Carrots, canned, no salt added, drained solids | 61.7 | – |
| 16 | burak ćwikłowy | pieczony | nie | `brak` | Beets, canned, drained solids | 59.7 | – |
| 21 | seler korzeniowy | pieczony | nie | `brak` | Celeriac, cooked, boiled, drained, without salt | 45.0 | – |
| 26 | pasternak | pieczony | nie | `brak` | Parsnips, cooked, boiled, drained, without salt | 45.0 | – |
| 29 | por | duszony | nie | `brak` | Leeks, (bulb and lower-leaf portion), freeze-dried | 72.6 | – |
| 32 | cebula | duszony | nie | `brak` | Onions, young green, tops only | 58.8 | – |
| 33 | cebula | pieczony | nie | `brak` | Onions, young green, tops only | 58.8 | – |
| 38 | czosnek | smażony | nie | `brak` | Garlic bread, frozen | 48.7 | – |
| 44 | kapusta biała | duszony | nie | `brak` | Cabbage, napa, cooked | 68.4 | – |
| 47 | kapusta czerwona | duszony | nie | `brak` | Cabbage, red, raw | 45.0 | – |
| 53 | kapusta kiszona | duszony | tak | `brak` | Sauerkraut, canned, solids and liquids | 61.1 | kiszona naturalnie; w USDA kapusta konserwowa |
| 57 | brukselka | pieczony | nie | `brak` | Brussels sprouts, cooked, boiled, drained, without salt | 45.0 | – |
| 61 | kalafior | pieczony | nie | `brak` | Cauliflower, green, cooked, no salt added | 69.6 | – |
| 65 | brokuł | pieczony | nie | `brak` | Broccoli, chinese, cooked | 66.7 | – |
| 72 | szpinak | duszony | nie | `brak` | Spinach, canned, no salt added, solids and liquids | 59.0 | – |
| 84 | pomidor | pieczony | nie | `brak` | Tomatoes, red, ripe, cooked | 75.0 | – |
| 91 | papryka czerwona | duszony | nie | `brak` | Peppers, sweet, red, freeze-dried | 70.7 | – |
| 92 | papryka czerwona | pieczony | nie | `brak` | Peppers, sweet, red, freeze-dried | 70.7 | – |
| 94 | papryka czerwona | grillowany | nie | `brak` | Peppers, sweet, red, freeze-dried | 70.7 | – |
| 98 | papryka żółta | pieczony | nie | `brak` | Peppers, sweet, yellow, raw | 45.0 | – |
| 102 | cukinia | duszony | nie | `brak` | Squash, summer, zucchini, includes skin, raw | 45.0 | – |
| 103 | cukinia | pieczony | nie | `brak` | Squash, summer, zucchini, includes skin, raw | 45.0 | – |
| 104 | cukinia | smażony | nie | `brak` | Squash, summer, zucchini, includes skin, raw | 45.0 | – |
| 105 | cukinia | grillowany | nie | `brak` | Squash, summer, zucchini, includes skin, raw | 45.0 | – |
| 107 | bakłażan | pieczony | nie | `brak` | Eggplant, raw | 45.0 | – |
| 108 | bakłażan | smażony | nie | `brak` | Plantains, green, fried | 46.9 | – |
| 109 | bakłażan | grillowany | nie | `brak` | Eggplant, raw | 45.0 | – |
| 112 | dynia | pieczony | nie | `brak` | Fish, sunfish, pumpkin seed, cooked, dry heat | 75.5 | – |
| 126 | kukurydza cukrowa (kolba) | grillowany | nie | `brak` | Corn, sweet, yellow, canned, cream style, no salt added | 61.0 | – |
| 131 | szparagi | grillowany | nie | `brak` | Asparagus, canned, drained solids | 63.0 | – |
| 133 | koper włoski (fenkuł) | pieczony | nie | `brak` | Fennel, bulb, raw | 45.0 | – |
| 136 | pak choi | smażony | nie | `brak` | Cabbage, chinese (pak-choi), raw | 45.0 | – |
| 149 | pieczarka | duszony | nie | `brak` | Mushrooms, white, raw | 45.0 | – |
| 151 | pieczarka | grillowany | nie | `brak` | Mushrooms, portabella, grilled | 74.6 | – |
| 153 | boczniak | smażony | nie | `brak` | Mushrooms, white, stir-fried | 74.1 | – |
| 158 | kurka | duszony | nie | `brak` | Mushrooms, Chanterelle, raw | 45.0 | – |
| 159 | kurka | smażony | nie | `brak` | Mushrooms, white, stir-fried | 61.0 | – |
| 162 | jabłko | pieczony | nie | `brak` | Potatoes, baked, skin, without salt | 51.5 | – |
| 215 | kasza gryczana niepalona (biała) | gotowany | tak | `brak` | Buckwheat | 75.0 | – |
| 255 | płatki owsiane | gotowany | nie | `brak` | Cereals, oats, regular and quick, not fortified, dry | 75.0 | – |
| 324 | białko jaja kurzego | gotowany | nie | `brak` | Egg, white, dried | 75.0 | – |
| 326 | żółtko jaja kurzego | gotowany | nie | `brak` | Egg, yolk, dried | 75.0 | – |
| 328 | jajo przepiórcze | gotowany | nie | `brak` | Egg, whole, cooked, hard-boiled | 54.0 | – |
| 334 | pierś z kurczaka | grillowany | nie | `brak` | Chicken, broiler or fryers, breast, skinless, boneless, meat only, cooked, grilled | 84.5 | – |
| 340 | udo z kurczaka | grillowany | nie | `brak` | Chicken, broilers or fryers, thigh, meat only, cooked, roasted | 75.0 | – |
| 345 | podudzie z kurczaka | grillowany | nie | `brak` | Chicken, broilers or fryers, dark meat, drumstick, meat only, cooked, roasted | 72.5 | – |
| 349 | skrzydełko z kurczaka | grillowany | nie | `brak` | Chicken, broilers or fryers, wing, meat and skin, cooked, roasted | 75.0 | – |
| 362 | mięso mielone z kurczaka | duszony | nie | `brak` | Chicken, roasting, giblets, cooked, simmered | 69.1 | – |
| 365 | pierś z indyka | duszony | nie | `brak` | Turkey, whole, neck, meat only, cooked, simmered | 78.0 | – |
| 367 | pierś z indyka | smażony | nie | `brak` | Chicken, broilers or fryers, breast, meat only, cooked, fried | 57.4 | – |
| 368 | pierś z indyka | grillowany | nie | `brak` | Turkey, whole, breast, meat only, cooked, roasted | 72.1 | – |
| 370 | udziec z indyka | duszony | nie | `brak` | Turkey, whole, neck, meat only, cooked, simmered | 80.2 | – |
| 373 | mięso mielone z indyka | duszony | nie | `brak` | Turkey, Ground, cooked | 75.0 | – |
| 374 | mięso mielone z indyka | smażony | nie | `brak` | Turkey, Ground, cooked | 75.0 | – |
| 386 | polędwiczka wieprzowa | smażony | nie | `brak` | Pork, fresh, loin, top loin (chops), boneless, separable lean only, cooked, pan-fried | 79.7 | – |
| 393 | łopatka wieprzowa | gotowany | nie | `brak` | Pork, fresh, shoulder, arm picnic, separable lean and fat, cooked, braised | 80.0 | – |
| 397 | szynka wieprzowa surowa | gotowany | nie | `brak` | Pork, fresh, leg (ham), whole, separable lean only, cooked, roasted | 80.0 | – |
| 398 | szynka wieprzowa surowa | duszony | nie | `brak` | Pork, fresh, loin, whole, separable lean only, cooked, braised | 71.9 | – |
| 401 | boczek surowy | pieczony | nie | `brak` | Pork, fresh, loin, whole, separable lean only, cooked, roasted | 68.5 | – |
| 402 | boczek surowy | smażony | nie | `brak` | Pork, fresh, loin, blade (chops), bone-in, separable lean only, cooked, pan-fried | 66.4 | – |
| 406 | żeberka wieprzowe | grillowany | nie | `brak` | Pork, fresh, loin, whole, separable lean and fat, cooked, broiled | 82.8 | – |
| 408 | golonka | gotowany | tak | `brak` | Pork, fresh, ground, cooked | 62.9 | w USDA tylko golonka marynowana |
| 409 | golonka | pieczony | tak | `brak` | Pork, cured, bacon, cooked, baked | 62.0 | w USDA tylko golonka marynowana |
| 411 | mięso mielone wieprzowe | duszony | nie | `brak` | Pork, fresh, ground, cooked | 75.0 | – |
| 412 | mięso mielone wieprzowe | smażony | nie | `brak` | Pork, fresh, ground, cooked | 75.0 | – |
| 415 | wątróbka wieprzowa | smażony | nie | `brak` | Beef, variety meats and by-products, liver, cooked, pan-fried | 45.2 | – |
| 417 | polędwica wołowa | pieczony | nie | `brak` | Beef, loin, tenderloin roast, boneless, separable lean only, trimmed to 0" fat, choice, cooked, roasted | 80.9 | – |
| 418 | polędwica wołowa | smażony | nie | `brak` | Beef, New Zealand, imported, tenderloin, separable lean only, cooked, fast fried | 83.2 | – |
| 421 | rostbef | pieczony | nie | `brak` | Beef, short loin, top loin, steak, separable lean only, trimmed to 1/8" fat, select, cooked, grilled | 70.5 | – |
| 422 | rostbef | smażony | nie | `brak` | Beef, short loin, top loin, steak, separable lean only, trimmed to 1/8" fat, select, cooked, grilled | 70.5 | – |
| 425 | antrykot | smażony | nie | `brak` | Beef, ribeye cap steak, boneless, separable lean only, trimmed to 0" fat, choice, cooked, grilled | 48.8 | – |
| 426 | antrykot | grillowany | nie | `brak` | Beef, ribeye cap steak, boneless, separable lean only, trimmed to 0" fat, choice, cooked, grilled | 83.8 | – |
| 428 | łopatka wołowa | gotowany | nie | `brak` | Beef, chuck, arm pot roast, separable lean only, trimmed to 0" fat, choice, cooked, braised | 75.0 | – |
| 434 | mostek wołowy | gotowany | nie | `brak` | Beef, brisket, flat half, separable lean only, trimmed to 0" fat, select, cooked, braised | 74.8 | – |
| 437 | mięso mielone wołowe | duszony | nie | `brak` | Beef, ground, 80% lean meat / 20% fat, crumbles, cooked, pan-browned | 69.8 | – |
| 446 | jagnięcina (udziec) | duszony | nie | `brak` | Lamb, shoulder, whole (arm and blade), separable lean only, trimmed to 1/4" fat, choice, cooked, braised | 27.3 | – |
| 448 | jagnięcina (udziec) | grillowany | nie | `brak` | Lamb, leg, whole (shank and sirloin), separable lean only, trimmed to 1/4" fat, choice, cooked, roasted | 51.8 | – |
| 459 | kiełbasa śląska | smażony | tak | `brak` | Polish sausage, pork | 75.0 | – |
| 460 | kiełbasa śląska | grillowany | tak | `brak` | Polish sausage, pork | 75.0 | – |
| 462 | kiełbasa wieprzowa wędzona | pieczony | nie | `brak` | Sausage, smoked link sausage, pork | 75.0 | – |
| 463 | kiełbasa wieprzowa wędzona | smażony | nie | `brak` | Sausage, smoked link sausage, pork | 75.0 | – |
| 464 | kiełbasa wieprzowa wędzona | grillowany | nie | `brak` | Sausage, smoked link sausage, pork | 75.0 | – |
| 465 | biała kiełbasa | surowy | tak | `brak` | Sausage, Italian, pork, mild, raw | 76.2 | – |
| 467 | biała kiełbasa | pieczony | tak | `brak` | Sausage, pork and beef, fresh, cooked | 68.2 | – |
| 474 | boczek wędzony | smażony | nie | `brak` | Pork, cured, bacon, unprepared | 75.0 | – |
| 478 | kaszanka | pieczony | tak | `brak` | Blood sausage | 75.0 | z kaszą; w USDA kiszka bez kaszy |
| 479 | kaszanka | smażony | tak | `brak` | Blood sausage | 75.0 | z kaszą; w USDA kiszka bez kaszy |
| 480 | kaszanka | grillowany | tak | `brak` | Blood sausage | 75.0 | z kaszą; w USDA kiszka bez kaszy |
| 483 | łosoś | gotowany na parze | nie | `brak` | Fish, salmon, Atlantic, farmed, cooked, dry heat | 80.0 | – |
| 485 | łosoś | smażony | nie | `brak` | Fish, croaker, Atlantic, cooked, breaded and fried | 51.7 | – |
| 489 | dorsz | gotowany | nie | `brak` | Fish, cod, Atlantic, cooked, dry heat | 80.0 | – |
| 490 | dorsz | gotowany na parze | nie | `brak` | Fish, cod, Atlantic, cooked, dry heat | 80.0 | – |
| 492 | dorsz | smażony | nie | `brak` | Fish, croaker, Atlantic, cooked, breaded and fried | 79.3 | – |
| 495 | mintaj | smażony | nie | `brak` | Fish, pollock, Alaska, cooked | 75.0 | – |
| 501 | tilapia | smażony | nie | `brak` | Fish, shark, mixed species, cooked, batter-dipped and fried | 53.3 | – |
| 504 | panga | smażony | tak | `brak` | Fish, catfish, channel, cooked, breaded and fried | 79.5 | – |
| 507 | pstrąg | smażony | nie | `brak` | Fish, trout, rainbow, farmed, raw | 45.0 | – |
| 512 | karp | smażony | nie | `brak` | Fish, croaker, Atlantic, cooked, breaded and fried | 60.3 | – |
| 517 | sandacz | smażony | nie | `brak` | Fish, pike, walleye, cooked, dry heat | 45.0 | w USDA pokrewny walleye |
| 519 | okoń | smażony | nie | `brak` | Fish, shark, mixed species, cooked, batter-dipped and fried | 78.0 | – |
| 524 | sola | smażony | nie | `brak` | Fish, flatfish (flounder and sole species), raw | 45.0 | – |
| 526 | tuńczyk świeży | smażony | nie | `brak` | Fish, tuna, yellowfin, fresh, cooked, dry heat | 45.0 | – |
| 534 | śledź | smażony | nie | `brak` | Fish, herring, Atlantic, kippered | 70.6 | – |
| 548 | krewetki | grillowany | nie | `brak` | Crustaceans, shrimp, cooked | 75.0 | – |
| 550 | kalmary | gotowany | nie | `brak` | Mollusks, clam, mixed species, cooked, moist heat | 84.0 | – |
| 567 | soczewica czerwona | gotowany | nie | `brak` | Lentils, mature seeds, cooked, boiled, without salt | 47.3 | – |
| 578 | tofu naturalne | pieczony | nie | `brak` | Tofu, firm, prepared with calcium sulfate and magnesium chloride (nigari) | 65.6 | – |
| 580 | tofu naturalne | grillowany | nie | `brak` | Tofu, firm, prepared with calcium sulfate and magnesium chloride (nigari) | 65.6 | – |
| 583 | tempeh | smażony | nie | `brak` | Tempeh, cooked | 75.0 | – |
