# Miary domowe – pokrycie

Wygenerowane przez `make portions` (S-109) z `data-pipeline/mapping/mapping.csv` i porcji USDA SR Legacy – nie edytuj ręcznie.

## Podsumowanie

| Warianty produktów | Liczba |
| --- | --- |
| na liście (`mapping.csv`) | 636 |
| z `fdc_id` | 482 |
| z co najmniej jedną miarą | 399 |
| ze szklanką i `ml` (gęstość) | 311 |
| z łyżką | 61 |
| z łyżeczką | 16 |
| z miarą sztukową (sztuka, plaster, liść…) | 216 |

Warianty bez `fdc_id` (status `brak`) nie mają porcji USDA. Szklanka (250 ml) i `ml` są wyliczane z gęstości (`calculated`), pozostałe miary pochodzą wprost z USDA (`measured`). Powtórzenia tej samej miary, rozmiaru i postaci pominięte: 13.

## Miary

| Miara | Wiersze |
| --- | --- |
| bulwa | 1 |
| cząstka | 8 |
| filet | 29 |
| gałązka | 3 |
| główka | 17 |
| kawałek | 7 |
| kolba | 4 |
| kotlet | 5 |
| krążek | 4 |
| liść | 19 |
| ml | 191 |
| pasek | 5 |
| pierś | 7 |
| plaster | 46 |
| podudzie | 6 |
| połówka | 1 |
| pęczek | 2 |
| różyczka | 3 |
| skrzydło | 1 |
| stek | 4 |
| szklanka | 395 |
| sztuka | 178 |
| udo | 6 |
| ziarno | 2 |
| ząbek | 1 |
| łodyga | 12 |
| łyżeczka | 18 |
| łyżka | 63 |

## Warianty z `fdc_id` bez miar (83)

| variant_id | Produkt | Wariant | fdc_id | Opis USDA |
| --- | --- | --- | --- | --- |
| 171 | jagoda (borówka czarna) | surowy | 167640 | Blueberries, wild, raw (Alaska Native) |
| 227 | kasza kuskus | gotowany | 169700 | Couscous, cooked |
| 252 | makaron ryżowy | surowy | 169742 | Rice noodles, dry |
| 262 | mąka pszenna pełnoziarnista | surowy | 168944 | Wheat flour, whole-grain, soft wheat |
| 280 | wafle ryżowe | gotowy | 170250 | Snacks, rice cakes, brown rice, plain, unsalted |
| 290 | jogurt grecki | gotowy | 171304 | Yogurt, Greek, plain, whole milk |
| 302 | ser gouda | gotowy | 171241 | Cheese, gouda |
| 303 | ser edamski | gotowy | 173419 | Cheese, edam |
| 308 | parmezan | gotowy | 170848 | Cheese, parmesan, hard |
| 350 | kurczak (tuszka) | surowy | 171447 | Chicken, broilers or fryers, meat and skin, raw |
| 356 | żołądki drobiowe | surowy | 171456 | Chicken, gizzard, all classes, raw |
| 361 | mięso mielone z kurczaka | surowy | 171116 | Chicken, ground, raw |
| 363 | mięso mielone z kurczaka | smażony | 171117 | Chicken, ground, crumbles, cooked, pan-browned |
| 369 | udziec z indyka | surowy | 171090 | Turkey, whole, dark meat, meat only, raw |
| 371 | udziec z indyka | pieczony | 174508 | Turkey, dark meat, meat only, with added solution, cooked, roasted |
| 372 | mięso mielone z indyka | surowy | 171505 | Turkey, Ground, raw |
| 375 | kaczka | surowy | 172410 | Duck, domesticated, meat only, raw |
| 377 | gęś | surowy | 172413 | Goose, domesticated, meat only, raw |
| 378 | gęś | pieczony | 172414 | Goose, domesticated, meat only, cooked, roasted |
| 381 | schab | pieczony | 167894 | Pork, fresh, loin, center rib (roasts), boneless, separable lean only, cooked, roasted |
| 384 | polędwiczka wieprzowa | surowy | 168249 | Pork, fresh, loin, tenderloin, separable lean only, raw |
| 385 | polędwiczka wieprzowa | pieczony | 168250 | Pork, fresh, loin, tenderloin, separable lean only, cooked, roasted |
| 390 | karkówka | pieczony | 168259 | Pork, fresh, shoulder, blade, boston (roasts), separable lean and fat, cooked, roasted |
| 392 | łopatka wieprzowa | surowy | 168255 | Pork, fresh, shoulder, arm picnic, separable lean and fat, raw |
| 394 | łopatka wieprzowa | duszony | 168256 | Pork, fresh, shoulder, arm picnic, separable lean and fat, cooked, braised |
| 396 | szynka wieprzowa surowa | surowy | 168224 | Pork, fresh, leg (ham), whole, separable lean only, raw |
| 400 | boczek surowy | surowy | 167812 | Pork, fresh, belly, raw |
| 403 | żeberka wieprzowe | surowy | 167853 | Pork, fresh, spareribs, separable lean and fat, raw |
| 404 | żeberka wieprzowe | duszony | 167854 | Pork, fresh, spareribs, separable lean and fat, cooked, braised |
| 405 | żeberka wieprzowe | pieczony | 169178 | Pork, fresh, spareribs, separable lean and fat, cooked, roasted |
| 407 | golonka | surowy | 169157 | Pork, pickled pork hocks |
| 410 | mięso mielone wieprzowe | surowy | 167902 | Pork, fresh, ground, raw |
| 413 | wątróbka wieprzowa | surowy | 167862 | Pork, fresh, variety meats and by-products, liver, raw |
| 414 | wątróbka wieprzowa | duszony | 167863 | Pork, fresh, variety meats and by-products, liver, cooked, braised |
| 416 | polędwica wołowa | surowy | 171803 | Beef, tenderloin, steak, separable lean only, trimmed to 1/8" fat, select, raw |
| 419 | polędwica wołowa | grillowany | 173117 | Beef, tenderloin, steak, separable lean only, trimmed to 1/8" fat, choice, cooked, broiled |
| 420 | rostbef | surowy | 173116 | Beef, short loin, top loin, steak, separable lean only, trimmed to 1/8" fat, choice, raw |
| 423 | rostbef | grillowany | 171805 | Beef, short loin, top loin, steak, separable lean only, trimmed to 1/8" fat, select, cooked, grilled |
| 424 | antrykot | surowy | 171735 | Beef, Australian, imported, grass-fed, rib, ribeye steak/roast lip-on, boneless, separable lean only, raw |
| 427 | łopatka wołowa | surowy | 174056 | Beef, chuck, arm pot roast, separable lean only, trimmed to 1/8" fat, choice, raw |
| 429 | łopatka wołowa | duszony | 170615 | Beef, chuck, arm pot roast, separable lean only, trimmed to 0" fat, choice, cooked, braised |
| 430 | pręga wołowa | surowy | 169441 | Beef, shank crosscuts, separable lean only, trimmed to 1/4" fat, choice, raw |
| 431 | pręga wołowa | gotowany | 169442 | Beef, shank crosscuts, separable lean only, trimmed to 1/4" fat, choice, cooked, simmered |
| 432 | pręga wołowa | duszony | 169442 | Beef, shank crosscuts, separable lean only, trimmed to 1/4" fat, choice, cooked, simmered |
| 433 | mostek wołowy | surowy | 174057 | Beef, brisket, flat half, separable lean only, trimmed to 1/8" fat, choice, raw |
| 436 | mięso mielone wołowe | surowy | 174036 | Beef, ground, 80% lean meat / 20% fat, raw |
| 438 | mięso mielone wołowe | smażony | 171799 | Beef, ground, 80% lean meat / 20% fat, crumbles, cooked, pan-browned |
| 439 | wątróbka wołowa | surowy | 169451 | Beef, variety meats and by-products, liver, raw |
| 441 | cielęcina (udziec) | surowy | 175269 | Veal, leg (top round), separable lean only, raw |
| 442 | cielęcina (udziec) | duszony | 175270 | Veal, leg (top round), separable lean only, cooked, braised |
| 443 | cielęcina (udziec) | pieczony | 173822 | Veal, leg (top round), separable lean only, cooked, roasted |
| 444 | cielęcina (udziec) | smażony | 175271 | Veal, leg (top round), separable lean only, cooked, pan-fried, breaded |
| 445 | jagnięcina (udziec) | surowy | 174313 | Lamb, leg, whole (shank and sirloin), separable lean only, trimmed to 1/4" fat, choice, raw |
| 447 | jagnięcina (udziec) | pieczony | 174314 | Lamb, leg, whole (shank and sirloin), separable lean only, trimmed to 1/4" fat, choice, cooked, roasted |
| 449 | królik | surowy | 172521 | Game meat, rabbit, domesticated, composite of cuts, raw |
| 450 | królik | duszony | 174346 | Game meat, rabbit, domesticated, composite of cuts, cooked, stewed |
| 451 | królik | pieczony | 172522 | Game meat, rabbit, domesticated, composite of cuts, cooked, roasted |
| 456 | pierś z kurczaka wędzona (wędlina) | gotowy | 172963 | Chicken breast, oven-roasted, fat-free, sliced |
| 457 | kiełbasa krakowska sucha | gotowy | 172954 | Sausage, Polish, pork and beef, smoked |
| 466 | biała kiełbasa | gotowany | 174579 | Sausage, pork and beef, fresh, cooked |
| 469 | parówki | gotowy | 172968 | Frankfurter, meat |
| 473 | boczek wędzony | gotowy | 168277 | Pork, cured, bacon, unprepared |
| 487 | łosoś wędzony | gotowy | 173687 | Fish, salmon, chinook, smoked |
| 493 | mintaj | surowy | 173725 | Fish, pollock, Alaska, raw |
| 525 | tuńczyk świeży | surowy | 175159 | Fish, tuna, fresh, yellowfin, raw |
| 527 | tuńczyk świeży | grillowany | 172006 | Fish, tuna, yellowfin, fresh, cooked, dry heat |
| 538 | tuńczyk w sosie własnym | gotowy | 171986 | Fish, tuna, light, canned in water, without salt, drained solids |
| 545 | krewetki | surowy | 175179 | Crustaceans, shrimp, raw |
| 546 | krewetki | gotowany | 175180 | Crustaceans, shrimp, cooked |
| 549 | kalmary | surowy | 174223 | Mollusks, squid, mixed species, raw |
| 551 | kalmary | smażony | 171982 | Mollusks, squid, mixed species, cooked, fried |
| 553 | małże | gotowany | 174217 | Mollusks, mussel, blue, cooked, moist heat |
| 560 | fasola czerwona konserwowa | gotowy | 174285 | Beans, kidney, red, mature seeds, canned, drained solids |
| 562 | bób | gotowany | 170378 | Broadbeans, immature seeds, cooked, boiled, drained, without salt |
| 565 | ciecierzyca konserwowa | gotowy | 173800 | Chickpeas (garbanzo beans, bengal gram), mature seeds, canned, drained solids |
| 582 | tempeh | gotowy | 172467 | Tempeh, cooked |
| 590 | orzechy nerkowca | surowy | 170162 | Nuts, cashew nuts, raw |
| 605 | nasiona chia | surowy | 170554 | Seeds, chia seeds, dried |
| 607 | sezam | pieczony | 170151 | Seeds, sesame seeds, whole, roasted and toasted |
| 610 | wiórki kokosowe | gotowy | 170170 | Nuts, coconut meat, dried (desiccated), not sweetened |
| 628 | czekolada gorzka (70%) | gotowy | 170273 | Chocolate, dark, 70-85% cacao solids |
| 634 | drożdże świeże | surowy | 175042 | Leavening agents, yeast, baker's, compressed |
| 635 | żelatyna | gotowy | 169599 | Gelatins, dry powder, unsweetened |

## Pominięte opisy porcji USDA

Liczone raz na rekord USDA i opis. „miara pominięta” – miara z listy `ignored` w `measures.yaml` (masa, opakowanie, porcja handlowa); „wydajność” – porcja z opakowania lub produktu przed obróbką; „nieznana miara” i „nieznane słowa” – do uzupełnienia słownika.

| Powód | Opisy |
| --- | --- |
| miara pominięta | 299 |
| nieznane słowa | 23 |
| wydajność | 13 |

| Powód | Miara lub słowa | Opisy |
| --- | --- | --- |
| miara pominięta | oz | 162 |
| miara pominięta | nlea serving | 21 |
| miara pominięta | unit | 18 |
| miara pominięta | lb | 15 |
| miara pominięta | cubic inch | 11 |
| miara pominięta | can | 10 |
| miara pominięta | package | 10 |
| miara pominięta | container | 8 |
| miara pominięta | serving | 7 |
| miara pominięta | roast | 6 |
| miara pominięta | packet | 4 |
| miara pominięta | cake | 2 |
| miara pominięta | chicken | 2 |
| miara pominięta | cracker | 2 |
| miara pominięta | duck | 2 |
| miara pominięta | goose | 2 |
| miara pominięta | patty | 2 |
| miara pominięta | baby ear | 1 |
| miara pominięta | bar | 1 |
| miara pominięta | block | 1 |
| miara pominięta | cakes | 1 |
| miara pominięta | cantaloupe balls | 1 |
| miara pominięta | dash | 1 |
| miara pominięta | each | 1 |
| miara pominięta | envelope | 1 |
| miara pominięta | g | 1 |
| miara pominięta | grams | 1 |
| miara pominięta | individual packet | 1 |
| miara pominięta | pat | 1 |
| miara pominięta | spear tip | 1 |
| miara pominięta | stick | 1 |
| miara pominięta | watermelon balls | 1 |
| nieznane słowa | cooked excluding refuse | 8 |
| nieznane słowa | cooked | 5 |
| nieznane słowa | snack size | 2 |
| nieznane słowa | arils seed juice sacs | 1 |
| nieznane słowa | brownulated | 1 |
| nieznane słowa | cherry tomatoes | 1 |
| nieznane słowa | foot long frankfurter roll | 1 |
| nieznane słowa | hamburger frankfurter onion roll bun large roll | 1 |
| nieznane słowa | or packet | 1 |
| nieznane słowa | or slice | 1 |
| nieznane słowa | raw | 1 |
| wydajność | cup with pits yields | 2 |
| wydajność | pint as purchased yields | 2 |
| wydajność | can yields | 1 |
| wydajność | cup dry yields | 1 |
| wydajność | cup in shell edible yield | 1 |
| wydajność | cup with hulls edible yield | 1 |
| wydajność | ear large yields | 1 |
| wydajność | ear medium yields | 1 |
| wydajność | oz dry yields | 1 |
| wydajność | package yields | 1 |
| wydajność | recipe yield | 1 |
