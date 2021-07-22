import ffx_rng_tracker

def predict_equipment_drops(damage_rolls_input, abilities, characters, steals_range, piranha_kills_range, kilika_in_kills_range, kilika_out_kills_range):

	def check_equipment(monster_name, killer_index, kilika_in_kills=0, sinscale_kills=0, kilika_out_kills=0):

		monster_name = monster_name.lower()

		*_, equipment = rng_tracker.get_spoils(monster_name, killer_index, rng_tracker.current_party_formation)

		if equipment:
			if equipment['type'] == 'weapon' and equipment['owner'] in characters:
				for ability in abilities:
					if ability in equipment['abilities']:

						scenario = {'equipment': equipment, 'steals': steals, 
									'piranha_kills': piranha_kills - 4, 'kilika_in_kills': kilika_in_kills, 
									'sinscale_kills': sinscale_kills, 'kilika_out_kills': kilika_out_kills}

						if scenario not in scenarios:
							scenarios.append(scenario)

	rng_tracker = ffx_rng_tracker.FFXRNGTracker(damage_rolls_input)

	scenarios = []

	# check for every possible number of steals
	for steals in range(steals_range[0], steals_range[1] + 1):

		# check every possible number of piranha kills + klikk and tros
		for piranha_kills in range(piranha_kills_range[0] + 4, piranha_kills_range[1] + 4 + 1):

			# check for kilika possible equipments to be from these enemies
			for kilika_enemy in ('killer_bee', 'dinonix', 'yellow_element'):

				# get the possible killers based on the enemy
				if kilika_enemy == 'killer_bee':		kilika_killers = (4, 7)
				elif kilika_enemy == 'dinonix':			kilika_killers = (0, 4, 7)
				elif kilika_enemy == 'yellow_element':	kilika_killers = (7,)
				else:									kilika_killers = (0, 4, 7)

				# check for kilika kills
				for kilika_killer in kilika_killers:

					# check for the different amounts of sinscale kills in the echuilles fight
					for sinscale_kills in (2, 4):

						# check for every possible number of kills before geneaux
						for kilika_in_kills in range(kilika_in_kills_range[0], kilika_in_kills_range[1] + 1):

							# check for every possible number of kills after geneaux
							for kilika_out_kills in range(kilika_out_kills_range[0], kilika_out_kills_range[1] + 1):

								# reset the rng positions
								rng_tracker.reset_variables()

								# 15 kills before klikk
								rng_tracker.rng_current_positions[10] += (15 + piranha_kills) * 3

								rng_tracker.rng_current_positions[10] += steals

								besaid_forced_kills = (	('dingo', 0),
														('condor', 4),
														('water_flan', 5),
														('???', 0),
														('garuda_3', 7),
														('dingo_2', 0),
														('condor_2', 4),
														('water_flan_2', 5)
														)

								rng_tracker.add_change_party_event('tywl')

								for enemy, killer_index in besaid_forced_kills:
									check_equipment(enemy, killer_index)

								boat_kilika_forced_kills = (	('sin', 7),
																('sinspawn_echuilles', 0),
																('ragora_2', 0)
																)

								rng_tracker.add_change_party_event('tykwl')

								for enemy, killer_index in boat_kilika_forced_kills:
									check_equipment(enemy, killer_index)

								for i in range(kilika_in_kills):
									check_equipment(kilika_enemy, kilika_killer, kilika_in_kills)

								kilika_forced_kills = (	('geneaux\'s_tentacle', 7),
														('geneaux\'s_tentacle', 7),
														('sinspawn_geneaux', 7)
														)

								for enemy, killer_index in kilika_forced_kills:
									check_equipment(enemy, killer_index, kilika_in_kills)

								for i in range(kilika_out_kills):

									# at least 4 kills in kilika
									if kilika_out_kills + kilika_in_kills < 4:
										kilika_out_kills = 4 - kilika_in_kills

									check_equipment(kilika_enemy, kilika_killer, kilika_in_kills, sinscale_kills, kilika_out_kills)

								luca_forced_kills = (	('Worker', 5),
														('Worker', 5),
														('Worker', 5),
														('Worker', 5),
														('Worker', 5),
														('Worker', 3),
														('Worker', 5),
														('Worker', 5),
														('Worker', 5),
														('Worker', 0),
														('Oblitzerator', 0)
														)

								for enemy, killer_index in luca_forced_kills:
									check_equipment(enemy, killer_index, kilika_in_kills, sinscale_kills, kilika_out_kills)

								# sahagin chiefs
								rng_tracker.rng_current_positions[10] += 17 * 3

								luca_miihen_forced_kills = (	('Vouivre_2', 2),
																('Garuda_2', 2),
																('Raldo_2', 2),
																)

								rng_tracker.add_change_party_event('tyakwl')

								for enemy, killer_index in luca_miihen_forced_kills:
									check_equipment(enemy, killer_index, kilika_in_kills, sinscale_kills, kilika_out_kills)

	return scenarios

if __name__ == '__main__':

	damage_rolls_input = input('Damage rolls (Auron1 Tidus1 A2 T2 A3 T3): ')

	# replace different symbols with spaces
	for symbol in (',', '-', '/', '\\'):
		damage_rolls_input = damage_rolls_input.replace(symbol, ' ')

	# fixes double spaces
	damage_rolls_input = ' '.join(damage_rolls_input.split())

	damage_rolls_input = tuple([int(damage_roll) for damage_roll in damage_rolls_input.split(' ')])

	abilities = ('Lightningstrike', 'Icestrike')
	characters = ('Tidus', 'Wakka')
	steals = (4, 9)
	piranha_kills = (0, 6)
	kilika_in_kills = (2, 7)
	kilika_out_kills = (0, 6)

	print(f'Testing all scenarios with '
		f'{steals[0]}-{steals[1]} steals, '
		f'{piranha_kills[0]}-{piranha_kills[1]} optional piranha kills, '
		f'2-4 Sinscales kills, '
		f'{kilika_in_kills[0]}-{kilika_in_kills[1]} Kilika(In) kills, '
		f'{kilika_out_kills[0]}-{kilika_out_kills[1]} Kilika(Out) kills '
		f'for weapon drops for {"/".join(characters)} in Besaid, Kilika and Luca '
		f'with at least 1 of these abilities: {", ".join(abilities)}')

	print('(Assuming no character deaths and no optional Ragora kills in Kilika)')

	good_equipments_scenarios = predict_equipment_drops(damage_rolls_input, abilities, characters, steals, piranha_kills, kilika_in_kills, kilika_out_kills)

	# if the list is not empty
	if good_equipments_scenarios:
		output = '------------------------------------------------------------------------------------------------------------------------\n'
		output += 'Steals | Piranhas | Sinscales | Kilika In | Kilika Out |          Enemy |  Killer | Owner | Abilities\n'
		output += '------------------------------------------------------------------------------------------------------------------------\n'
		for scenario in good_equipments_scenarios:

			scenario['killer'] = (	'Tidus' if scenario['equipment']['killer_index'] == 0 else 
									'Yuna' if scenario['equipment']['killer_index'] == 1 else 
									'Auron' if scenario['equipment']['killer_index'] == 2 else 
									'Kimahri' if scenario['equipment']['killer_index'] == 3 else 
									'Wakka' if scenario['equipment']['killer_index'] == 4 else 
									'Lulu' if scenario['equipment']['killer_index'] == 5 else 
									'Rikku' if scenario['equipment']['killer_index'] == 6 else 
									'Valefor'  if scenario['equipment']['killer_index'] == 7 else 
									'???'
									)

			output += f'{scenario["steals"]:>6} | {scenario["piranha_kills"]:>8} | '
			output += f'{scenario["sinscale_kills"]:>9} | '
			output += f'{scenario["kilika_in_kills"]:>9} | '
			output += f'{scenario["kilika_out_kills"]:>10} | '
			output += f'{scenario["equipment"]["monster_name"]:>14} | {scenario["killer"]:>7} | {scenario["equipment"]["owner"]:>5} | '
			output += f'{", ".join(scenario["equipment"]["abilities"])}\n'

		output += '------------------------------------------------------------------------------------------------------------------------'
		print(output)

	else:
		print(f'No weapons found')
