<!-- https://blog.kulturbanause.de/2013/12/css-grid-layout-module/ -->
<template>
	<div class="schnipsl-player">
		<div id="name">{{ movie_info.title }}</div>
		<div id="series">{{ movie_info.category }}</div>
		<div id="provider">{{ movie_info.provider }}</div>
		<div id="day">
			{{ localDate(movie_info.timestamp, $t("locale_date_format")) }}
		</div>
		<div id="time">{{ duration(movie_info.current_time) }}</div>
		<div id="duration">{{ duration(movie_info.duration) }}</div>
		<div id="show">
			<v-btn icon @click="description_show = !description_show">
				<v-icon>{{
					description_show ? "mdi-chevron-up" : "mdi-chevron-down"
				}}</v-icon>
			</v-btn>
		</div>
		<div id="volume">
			<v-btn icon class="mx-4" @click="volume_dialog_show = true">
				<v-icon size="24px">mdi-volume-high</v-icon>
			</v-btn>
		</div>
		<div id="device">
			<v-btn icon class="mx-4" @click="device_dialog_show = true">
				<v-icon size="24px">mdi-television-classic</v-icon>
			</v-btn>
		</div>
		<div id="prev">
			<v-btn icon class="mx-4" @click="player_key('prev')">
				<v-icon size="24px">mdi-skip-previous</v-icon>
			</v-btn>
		</div>
		<div id="minus5">
			<v-btn icon class="mx-4" @click="player_key('minus5')">
				<v-icon size="24px">mdi-rewind-5</v-icon>
			</v-btn>
		</div>
		<div id="play">
			<v-btn icon class="mx-4" @click="player_key('play')">
				<v-icon>{{ player_pos.play ? "mdi-pause" : "mdi-play" }}</v-icon>
			</v-btn>
		</div>
		<div id="plus5">
			<v-btn icon class="mx-4" @click="player_key('plus5')">
				<v-icon size="24px">mdi-fast-forward-5</v-icon>
			</v-btn>
		</div>
		<div id="stop">
			<v-btn icon class="mx-4" @click="player_key('stop')">
				<v-icon size="24px">mdi-stop</v-icon>
			</v-btn>
		</div>
		<div id="bed">
			<v-btn
				icon
				class="mx-4"
				v-if="movie_info.recordable"
				@click="stop_and_record_dialog_show = true"
			>
				<v-icon size="24px">mdi-bed</v-icon>
			</v-btn>
		</div>
		<div id="position">
			<v-btn icon class="mx-4" @click="position_dialog_show = true">
				<v-icon size="24px">mdi-progress-clock</v-icon>
			</v-btn>
		</div>
		<v-expand-transition>
			<div id="description" v-show="description_show">
				{{ movie_info.description }}
			</div>
		</v-expand-transition>
		<div id="dialogs">
			<v-dialog dark v-model="volume_dialog_show" min-width="98vw">
				<v-card>
					<v-card-title class="justify-center">{{ $t("player_volume") }}</v-card-title>
					<v-divider></v-divider>
					<v-card-text>
	<!--
							<v-slider
								v-model="player_pos.volume"
								prepend-icon="mdi-volume-low"
								append-icon="mdi-volume-high"
								@click="player_volume()"
							></v-slider>
	-->
							<round-slider
								v-model="volume"
								start-angle="315"
								end-angle="+270"
								line-cap="round"
								:drag="player_volume()"
							/>
					</v-card-text>
				</v-card>
			</v-dialog>
			<v-dialog dark v-model="position_dialog_show"  min-width="98vw">
				<v-card>
					<v-card-title class="justify-center">{{ $t("player_position") }}</v-card-title>
					<v-divider></v-divider>
					<v-card-text>
	<!-- 
						{{ duration(player_pos.current_time) }}
						<v-slider v-model="sliderPosition" append-icon="mdi-timer"></v-slider>
						{{ duration(movie_info.duration - player_pos.current_time) }}
	-->
							<round-slider
								v-model="sliderPosition"
								start-angle="315"
								end-angle="+270"
								line-cap="round"
								:max=player_pos.duration
								:tooltipFormat="formatPosition"
							/>
					</v-card-text>
				</v-card>
			</v-dialog>
			<v-dialog dark v-model="device_dialog_show" scrollable max-width="300px">
				<v-card>
					<v-card-title>{{
						$t("player_select_device_dialog_header")
					}}</v-card-title>
					<v-divider></v-divider>
					<v-card-text style="height: 300px">
						<v-radio-group v-model="device_info.actual_device" column>
							<v-radio
								v-for="item in device_info.devices"
								:value="item"
								:label="item"
								:key="item"
								:checked="(item = device_info.actual_device)"
							></v-radio>
						</v-radio-group>
					</v-card-text>
					<v-divider></v-divider>
					<v-card-actions>
						<v-btn
							color="blue darken-1"
							text
							@click="device_dialog_show = false"
							>{{ $t("player_select_device_dialog_cancel") }}</v-btn
						>
						<v-btn color="blue darken-1" text @click="player_select_device()">{{
							$t("player_select_device_dialog_select")
						}}</v-btn>
					</v-card-actions>
				</v-card>
			</v-dialog>
			<v-dialog dark
				v-model="stop_and_record_dialog_show"
				scrollable
				max-width="300px"
			>
				<v-card>
					<v-card-title>{{
						$t("player_stop_and_record_dialog_header")
					}}</v-card-title>
					<v-divider></v-divider>
					<v-card-actions>
						<v-btn
							color="blue darken-1"
							text
							@click="stop_and_record_dialog_show = false"
							>{{ $t("player_stop_and_record_dialog_cancel") }}</v-btn
						>
						<v-btn
							color="blue darken-1"
							text
							@click="stopAndRecord(movie_info.uri)"
							>{{ $t("player_stop_and_record_dialog_select") }}</v-btn
						>
					</v-card-actions>
				</v-card>
			</v-dialog>
		</div>
	</div>
</template>
<script>
import messenger from "../messenger";
import RoundSlider from 'vue-round-slider'
import dayjs from "dayjs";
import dayjsPluginUTC from 'dayjs-plugin-utc'
dayjs.extend(dayjsPluginUTC, { parseToLocal: true })

export default {
	name: "player",
	components: {
		RoundSlider
	},
	data() {
		return {
			player_pos: {
				play: false,
				current_time: 55,
				duration: 120,
				volume: 3,
			},
			volume_old: 0,
			volume: 0,
			movie_info: {
				title: "Titel",
				category: "Typ",
				provider: "provider",
				timestamp: 123456,
				duration: 120,
				current_time: 65,
				description: "Beschreibung",
			},
			device_info: {
				actual_device: "",
				devices: ["TV Wohnzimmer", "TV Küche", "Chromecast Büro"],
			},
			description_show: false,
			volume_dialog_show: false,
			position_dialog_show: false,
			device_dialog_show: false,
			stop_and_record_dialog_show: false,
		};
	},
	created() {
		messenger.register(
			"player",
			this.messenger_onMessage,null, null);
	},
	methods: {
		messenger_onMessage(type, data) {
			console.log("incoming message to player", type, data);
			if (type == "player_position") {
				this.player_pos = data
				if (this.volume!=this.player_pos.volume){
				this.volume=this.player_pos.volume
				}
			}
			if (type == "player_movie_info") {
				this.movie_info = data;
			}
			if (type == "player_device_info") {
				this.uri = data.movie_uri;
				this.device_info.devices = data.devices;
				// force the dialog for now
				// better would be: If actual device is not in devices...
				this.device_info.actual_device = null;
				if (!this.device_info.actual_device) {
					this.device_dialog_show = true;
				}
			}
		},
		player_key(id) {
			console.log("Send key");
			messenger.emit("player_key", { keyid: id });
		},
		player_volume() {
			if (this.volume_old==this.volume){ // for unknown reason this routine is triggered all the time- so we try to supress the effect here
				return
			}
			console.log("Send volume", this.volume);
			messenger.emit("player_volume", {
				timer_vol: this.volume,
			});
			this.volume_old=this.volume
		},
		formatPosition(){
			return this.duration(this.player_pos.current_time)
		},
		player_select_device() {
			console.log("Send device");
			this.device_dialog_show = false;
			if (this.device_info.actual_device != "") {
				messenger.emit("select_player_device", {
					timer_dev: this.device_info.actual_device,
					uri: this.uri,
				});
			}
		},
		localDate(timestamp, locale) {
			return dayjs.unix(timestamp).local().format(locale);
		},
		duration(secondsValue) {
			var seconds = parseInt(secondsValue, 10);
			if (!Number.isInteger(seconds) || seconds < 0) {
				return "";
			}
			if (seconds < 3600) {
				return dayjs.unix(seconds).utc().format("mm:ss");
			} else {
				return dayjs.unix(seconds).utc().format("HH:mm:ss");
			}
		},
		stopAndRecord(uri) {
			console.log("stopAndRecord", uri);
			this.stop_and_record_dialog_show = false;
			messenger.emit("player_stop_and_record", {
				uri: uri,
			});
		},
	},
	computed: {
		sliderPosition: {
			// getter
			get: function () {
				if (
					this.player_pos.current_time >= 0 &&
					this.player_pos.duration > 0
				) {
					return parseInt(this.player_pos.current_time);
				} else {
					return NaN;
				}
			},
			// setter
			set: function (newValue) {
				console.log("Send timer by setter",newValue);
				this.player_pos.current_time = newValue;
				messenger.emit("player_time", {
					timer_pos: newValue,
				});
			},
		},
	},
};
</script>

<style scoped>
.schnipsl-player {
	display: grid;
	grid-template-columns: repeat(9, 9vw);
	grid-template-rows: repeat(5, min-content);
	gap: 0px 0px;
	grid-template-areas:
		"name name name name name name name name name"
		"series series series series series series series series series"
		"provider provider day day time time duration duration show"
		"volume device prev minus5 play plus5 stop bed position"
		"description description description description description description description description description"
		"dialogs dialogs dialogs dialogs dialogs dialogs dialogs dialogs dialogs";
	background: grey;
	border-radius: 10px;
	padding: 5px;
	margin-bottom: 10px;
	max-width: 98vw;
}

#marker {
	background: rgb(255, 0, 0);
	grid-area: marker;
	border-radius: 5px;
}
#name {
	background: grey;
	color: white;
	grid-area: name;
	font-family: "Atkinson-Hyperlegible", Helvetica, Arial;
	font-size: 200%;
	line-height: 100%;
	text-align: left;
	padding-left: 5px;
	font-weight: bold;
}
#series {
	background: grey;
	color: white;
	grid-area: series;
	font-family: "Atkinson-Hyperlegible", Helvetica, Arial;
	font-size: 150%;
	text-align: left;
	padding-left: 5px;
}
#provider {
	background: grey;
	color: lightgray;
	font-weight: bold;
	grid-area: provider;
	text-align: left;
	padding-left: 5px;
}
#day {
	background: grey;
	color: lightgray;
	font-weight: bold;
	grid-area: day;
}
#time {
	background: grey;
	color: lightgray;
	font-weight: bold;
	grid-area: time;
}
#duration {
	background: grey;
	color: lightgray;
	font-weight: bold;
	grid-area: duration;
}
#next {
	background: grey;
	color: white;
	grid-area: next;
	font-family: "Atkinson-Hyperlegible", Helvetica, Arial;
	font-size: 100%;
	text-align: left;
	padding-left: 5px;
}

#volume {
	background: grey;
	/*border-radius: 13px;*/
	/* (height of inner div) / 2 + padding */
	padding: 3px;
	grid-area: volume;
}

#position {
	background: grey;
	/*border-radius: 13px;*/
	/* (height of inner div) / 2 + padding */
	padding: 3px;
	grid-area: position;
}

#viewed {
	background: grey;
	/*border-radius: 13px;*/
	/* (height of inner div) / 2 + padding */
	padding: 3px;
	grid-area: viewed;
}

#viewed > div {
	background-color: orange;
	width: 40%;
	/* Adjust with JavaScript */
	height: 20px;
	border-radius: 10px;
}

#edit {
	background: grey;
	color: white;
	grid-area: edit;
}
#share {
	background: grey;
	color: white;
	grid-area: share;
}
#record {
	background: grey;
	color: white;
	grid-area: record;
}
#show {
	background: grey;
	color: white;
	grid-area: show;
}
#description {
	background: grey;
	color: white;
	grid-area: description;
}
.v-icon {
	color:rgb(13, 65, 207)
}
</style>