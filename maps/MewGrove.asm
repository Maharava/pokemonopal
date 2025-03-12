	object_const_def
	const MEWGROVE_MEW

MewGrove_MapScripts:
	def_scene_scripts

	def_callbacks

MewGroveMewScript:
	faceplayer
	opentext
	writetext MewEventText
	waitbutton
	closetext
	pause 20
	showemote EMOTE_SHOCK, PLAYER, 20
	loadwildmon MEW, 30
	setevent MEW_ENCOUNTERED
	startbattle
	disappear MEWGROVE_MEW
	reloadmapafterbattle
	end
	
MewEventText:
	text "...Mew...?"
	done


MewGrove_MapEvents:
	db 0, 0 ; filler

	def_warp_events
	warp_event  0, 4, ILEX_FOREST, 4
	warp_event  0, 5, ILEX_FOREST, 5

	def_coord_events

	def_bg_events

	def_object_events
	object_event 5, 5, SPRITE_POKE_BALL, SPRITEMOVEDATA_STILL, 0, 0, -1, -1, 0, OBJECTTYPE_SCRIPT, 0, MewGroveMewScript, MEW_ENCOUNTERED