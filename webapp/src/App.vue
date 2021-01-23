<template>
	<v-app toolbar footer dark>
		<!-- Provides the application the proper gutter -->
		<v-main>
			<v-container>
				<router-view />
			</v-container>
		</v-main>
		<v-row justify="center">
			<v-dialog v-model="device_dialog_show" scrollable max-width="300px">
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
			<v-dialog
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
		</v-row>
		<v-row justify="center">
			<v-dialog v-model="offline_dialog_show" max-width="300px">
				<v-card>
					<v-card-title>{{ $t("main_noconnect") }}</v-card-title>
					<v-divider></v-divider>
					<v-card-text style="height: 75px">
						<v-progress-circular
							indeterminate
							color="primary"
						></v-progress-circular>
					</v-card-text>
				</v-card>
			</v-dialog>
		</v-row>
		<v-snackbar v-model="snackbar">
			{{ user_message }}

			<template v-slot:action="{ attrs }">
				<v-btn color="pink" text v-bind="attrs" @click="snackbar = false">
					Close
				</v-btn>
			</template>
		</v-snackbar>

		<v-footer app>
			<player
				v-bind:app_player_pos="app_player_pos"
				v-bind:movie_info="movie_info"
			/>
		</v-footer>
	</v-app>
</template>

<script>
import Player from "./components/Player.vue";
import messenger from "./messenger";
import dayjs from "dayjs";
export default {
	components: {
		Player,
	},
	data() {
		return {
			app_player_pos: {
				play: false,
				current_time: 55,
				duration: 120,
				volume: 3,
			},
			movie_info: {
				title: "Titel",
				category: "Typ",
				provider: "provider",
				timestamp: 123456,
				duration: 120,
				current_time: 65,
				description: "Beschreibung",
			},
			uri: null,
			device_info: {
				actual_device: "",
				devices: ["TV Wohnzimmer", "TV Küche", "Chromecast Büro"],
			},
			device_dialog_show: false,
			offline_dialog_show: false,
			stop_and_record_dialog_show: false,
			show: false,
			snackbar: false,
			user_message: "",
		};
	},
	created() {
		messenger.register(
			"app",
			this.messenger_onMessage,
			this.messenger_onWSConnect,
			this.messenger_onWSClose
		);
	},
	methods: {
		messenger_onMessage(type, data) {
			console.log("incoming message to app", type, data);
			if (type == "app_player_pos") {
				this.app_player_pos = data;
			}
			if (type == "app_movie_info") {
				this.movie_info = data;
			}
			if (type == "app_user_message") {
				this.user_message = data.message;
				this.snackbar = true;
			}
			if (type == "app_device_info") {
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
		messenger_onWSConnect() {
			this.showDisconnect(false);
		},
		showDisconnect(disconnected) {
			console.log("websocket disconnect?:", disconnected);
			this.offline_dialog_show = disconnected;
		},
		messenger_onWSClose() {
			this.showDisconnect(true);
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
			return dayjs.unix(timestamp).format(locale);
		},
		duration(secondsValue) {
			var seconds = parseInt(secondsValue, 10);
			if (!Number.isInteger(seconds) || seconds < 0) {
				return "";
			}
			if (seconds < 3600) {
				return dayjs.unix(seconds).format("mm:ss");
			} else {
				return dayjs.unix(seconds).format("HH:mm:ss");
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
	provide: function () {
		return {
			localDate: this.localDate,
			duration: this.duration,
			stopAndRecord: this.stopAndRecord,
		};
	},
};
</script>


<style lang="scss">
#app {
	font-family: Avenir, Helvetica, Arial, sans-serif;
	-webkit-font-smoothing: antialiased;
	-moz-osx-font-smoothing: grayscale;
	text-align: center;
	color: #2c3e50;
}

#nav {
	padding: 30px;

	a {
		font-weight: bold;
		color: #2c3e50;

		&.router-link-exact-active {
			color: #42b983;
		}
	}
	@font-face {
		font-family: "Atkinson-Hyperlegible";
		src: local("Atkinson-Hyperlegible"),
			url(./fonts/Atkinson-Hyperlegible/Atkinson-Hyperlegible-Regular-102.ttf)
				format("truetype");
	}
}
</style>
