// https://stackoverflow.com/questions/49501873/css-grid-items-based-on-minimum-width-and-percentage

<template>
	<v-card dark>
		<v-toolbar>
			<v-app-bar-nav-icon @click="nav2Set()"></v-app-bar-nav-icon>

			<v-toolbar-title>{{ $t("main_title") }}</v-toolbar-title>

			<v-spacer></v-spacer>

			<v-btn icon @click="nav2Edit(0, null)">
				<v-icon>mdi-plus-circle</v-icon>
			</v-btn>
		</v-toolbar>
		<v-tabs grow>
			<v-tab>	{{ $t("main_streams") }}	</v-tab>
			<v-tab>	{{ $t("main_records") }}	</v-tab>
			<v-tab>	{{ $t("main_templates") }}	</v-tab>
			<v-tab>	{{ $t("main_timers") }}		</v-tab>
			<v-tab-item>
				<live-card v-for="item in movie_list.streams" :key="item.uuid" :item="item" />
			</v-tab-item>
			<v-tab-item>
				<record-card v-for="item in movie_list.records" :key="item.uuid" :item="item" />
			</v-tab-item>
			<v-tab-item>
				<quick-search-card v-for="item in movie_list.templates" :key="item.uuid" :item="item" />
			</v-tab-item>
			<v-tab-item>
					<timer-card v-for="item in movie_list.timers" :key="item.uuid" :item="item" />
		</v-tab-item>
		</v-tabs>
	</v-card>
</template>


<script>
import router from "../router";
import messenger from "../messenger";
import dayjs from "dayjs";
import LiveCard from "./LiveCard.vue";
import RecordCard from "./RecordCard.vue";
import TimerCard from "./TimerCard.vue";
import QuickSearchCard from "./QuickSearchCard.vue";

export default {
	name: "Schnipsl",
	components: {
		LiveCard,
		RecordCard,
		TimerCard,
		QuickSearchCard
	},
	title() {
		return `${this.name}`;
	},
	data() {
		return {
			movie_list: {
				templates: [
					{
						uuid: "1",
						icon: "mdi-magnify",
						iconClass: "red lighten-1 white--text",
						current_time: 0,
						movie_info: {
							title: "Titel",
							category: "Typ",
							provider: "Quelle",
							timestamp: "Datum",
							duration: "Dauer",
						},
					},
					{
						uuid: "2",
						icon: "mdi-magnify",
						iconClass: "red lighten-1 white--text",
						current_time: 10,
						movie_info: {
							title: "Titel-2",
							category: "Typ",
							provider: "Quelle",
							timestamp: "Datum",
							duration: "Dauer",
						},
					},
				],
				records: [
					{
						uuid: "3",
						icon: "mdi-play-pause",
						iconClass: "blue white--text",
						current_time: 20,
						movie_info: {
							title: "Titel-Stream",
							category: "Typ",
							provider: "Quelle",
							timestamp: "Datum",
							duration: "Dauer",
						},
					},
				],
				streams: [
					{
						uuid: "4",
						icon: "mdi-radio-tower",
						iconClass: "green lighten-1 white--text",
						current_time: "geschaut",
						movie_info: {
							title: "Titel-Stream",
							category: "Typ",
							provider: "Quelle",
							timestamp: "Datum",
							duration: "Dauer",
						},
					},
				],
				timers: [
					{
						uuid: "5",
						icon: "mdi-clock",
						iconClass: "amber white--text",
						current_time: "geschaut",
						movie_info: {
							title: "Titel-Timer",
							category: "Typ",
							provider: "Quelle",
							timestamp: "Datum",
							duration: "Dauer",
						},
					},
				],
			}
		};
	},
	created() {
		messenger.register("home", this.messenger_onMessage, null, null);

		if (localStorage.userName) {
			var username = localStorage.userName;
			messenger.init(username, "bla", "register");
		} else {
			this.nav2Set();
		}
	},
	methods: {
		nav2Set() {
			router.push({ name: "Settings" });
		},
		nav2Edit(uuid, query, item) {
			console.log("click for edit", item, query);
			router.push({ name: "Edit", params: { uuid: uuid, query: query } });
		},
		nav2Play(uri) {
			console.log("click for Play uri", uri);
			messenger.emit("home_play_request", { uri: uri });
		},
		requestRecordAdd(uri) {
			console.log("click for record uri", uri);
			messenger.emit("home_record_request", { uri: uri });
		},
		share(uuid) {
			console.log("click for share", uuid);
		},
		messenger_onMessage(type, data) {
			console.log("incoming message to home", type, data);
			if (type == "home_movie_info_list") {
				this.movie_list = data;
			}
			if (type == "home_movie_info_update") {
				var uuid = data.uuid;
				this.movie_list.records.forEach(function (movie_list_item) {
					if (movie_list_item.uuid == uuid) {
						//replace movie_info
						console.log("home_movie_info_update records");
						movie_list_item.current_time = data.current_time;
						movie_list_item.movie_info = data.movie_info;
					}
				});
				this.movie_list.streams.forEach(function (movie_list_item) {
					if (movie_list_item.uuid == uuid) {
						//replace movie_list_item
						console.log("home_movie_info_update streams");
						movie_list_item.current_time = data.current_time;
						movie_list_item.movie_info = data.movie_info;
					}
				});
				this.movie_list.templates.forEach(function (movie_list_item) {
					if (movie_list_item.uuid == uuid) {
						//replace movie_list_item
						console.log("home_movie_info_update templates");
						movie_list_item.current_time = data.current_time;
						movie_list_item.movie_info = data.movie_info;
					}
				});
				this.movie_list.timers.forEach(function (movie_list_item) {
					if (movie_list_item.uuid == uuid) {
						//replace movie_list_item
						console.log("home_movie_info_update timers");
						movie_list_item.current_time = data.current_time;
						movie_list_item.movie_info = data.movie_info;
					}
				});

				this.movie_list[data.uuid] = data;
			}
		},
		localDateTime(timestamp, locale) {
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
		localMinutes(secondsValue) {
			var seconds = parseInt(secondsValue, 10);
			if (!Number.isInteger(seconds || seconds < 0)) {
				return "";
			}
			if (seconds < 3600) {
				return dayjs.unix(seconds).format("mm [min]");
			} else {
				return dayjs.unix(seconds).format("HH:mm");
			}
		},
		progress(viewed, duration) {
			console.log("progress",viewed,duration)
			return viewed*100 / duration
		}
	},
	provide: function () {
		return {
			nav2Edit: this.nav2Edit,
			nav2Play: this.nav2Play,
			requestRecordAdd: this.requestRecordAdd,
			share: this.share,
			localDateTime: this.localDateTime,
			duration: this.duration,
			localMinutes: this.localMinutes,
			progress: this.progress
		};
	},
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h1,
h2 {
	font-weight: normal;
}
ul {
	list-style-type: none;
	padding: 0;
}
li {
	display: inline-block;
	margin: 0 10px;
}
a {
	color: #42b983;
}
</style>
