<template>
	<!-- Grid card layout für die gefundenen Einträge? Kuckst Du hier https://codepen.io/munieru_jp/pen/jpdJNV-->

	<v-card>
		<v-toolbar color="yellow">
			<v-toolbar-items>
				<v-btn icon @click="edit_delete_dialog_show = true">
					<v-icon>mdi-delete</v-icon>
				</v-btn>
				<v-divider vertical></v-divider>
			</v-toolbar-items>
			<v-spacer></v-spacer>
			<v-toolbar-title>{{ $t("edit_select_header") }}</v-toolbar-title>
		</v-toolbar>
		<v-container>
			<v-form ref="edit_select">
				<v-row>
					<v-col>
						<v-text-field
							v-model="query.name"
							:label="$t('edit_select_name')"
						></v-text-field>
					</v-col>
					<v-col>
						<v-switch
							v-model="query.recording"
							:label="$t('edit_select_recording')"
							color="orange"
							value="True"
							hide-details
						></v-switch>
					</v-col>
				</v-row>
				<v-row>
					<v-col>
						<v-autocomplete
							v-model="query.source_values"
							:items="query.source_items"
							outlined
							chips
							small-chips
							:label="$t('edit_select_source')"
							multiple
							@input="edit_query_available_providers()"
						></v-autocomplete>
					</v-col>
					<v-col>
						<v-autocomplete
							v-model="query.provider_values"
							:items="query.provider_items"
							outlined
							chips
							small-chips
							:label="$t('edit_select_provider')"
							multiple
							@input="edit_query_available_categories()"
						></v-autocomplete>
					</v-col>
				</v-row>
				<v-row>
					<v-col>
						<v-autocomplete
							v-model="query.category_values"
							:items="query.category_items"
							outlined
							chips
							small-chips
							:label="$t('edit_select_category')"
							multiple
						></v-autocomplete>
					</v-col>
				</v-row>
				<v-row>
					<v-btn
						icon
						@click="edit_query_available_movies(prev_page)"
						:disabled="this.prev_page < 0"
					>
						<v-icon>mdi-chevron-left</v-icon>
					</v-btn>
					<v-spacer></v-spacer>
					<v-text-field
						v-model="query.searchtext"
						:label="$t('edit_select_searchtext')"
						clearable
						@change="edit_query_available_movies(0)"
					></v-text-field>
					<v-btn
						icon
						@click="edit_query_available_movies(0)"
					>
						<v-icon>mdi-magnify</v-icon>
					</v-btn>
					<v-spacer></v-spacer>
					<v-btn
						icon
						@click="edit_query_available_movies(next_page)"
						:disabled="this.next_page < 0"
					>
						<v-icon>mdi-chevron-right</v-icon>
					</v-btn>
				</v-row>
			</v-form>
		</v-container>
		<v-list>
			<v-list-item v-for="movie_info in movie_info_list" :key="movie_info.uri">
				<v-list-item-content
					v-on="
						movie_info.streamable
							? { click: () => requestPlay(movie_info.uri) }
							: {}
					"
				>
					<v-list-item-title
						v-text="movie_info.title + ' • ' + movie_info.category"
					></v-list-item-title>
					<v-list-item-subtitle
						v-text="
							movie_info.provider +
							' • ' +
							localDate(movie_info.timestamp, $t('locale_date_time_format')) +
							' • ' +
							duration(movie_info.duration)
						"
					></v-list-item-subtitle>
					<v-expand-transition>
						<div v-show="movie_info.description_show">
							<v-divider></v-divider>

							<v-card-text>{{ movie_info.description }}</v-card-text>
						</div>
					</v-expand-transition>
				</v-list-item-content>

				<v-list-item-action>
					<v-btn
						icon
						class="mx-4"
						v-if="movie_info.streamable"
						@click="requestPlayAdd(movie_info.uri)"
					>
						<v-icon size="24px">mdi-video-plus</v-icon>
					</v-btn>
					<v-btn
						icon
						class="mx-4"
						v-if="movie_info.recordable"
						@click="requestRecordAdd(movie_info.uri)"
					>
						<v-icon size="24px">mdi-record</v-icon>
					</v-btn>
					<v-btn
						icon
						@click="movie_info.description_show = !movie_info.description_show"
					>
						<v-icon>{{
							movie_info.description_show
								? "mdi-chevron-up"
								: "mdi-chevron-down"
						}}</v-icon>
					</v-btn>
				</v-list-item-action>
			</v-list-item>
		</v-list>
		<v-row justify="center">
			<v-dialog dark v-model="waitSearchResults" max-width="300px">
				<!--<v-dialog  max-width="300px"> -->
				<v-card>
					<v-card-title>{{ $t("edit_wait_for_search") }}</v-card-title>
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
	</v-card>
</template>

<script>
import router from "../router";
import messenger from "../messenger";
import dayjs from "dayjs";
import dayjsPluginUTC from "dayjs-plugin-utc";
dayjs.extend(dayjsPluginUTC, { parseToLocal: true });

export default {
	name: "Edit",
	data: () => ({
		uuid: 0,
		query: {},
		movie_info_list: [],
		prev_page: -1,
		query_start_page: 0,
		next_page: -1,
	}),
	computed: {
		waitSearchResults: function () {
			return this.movie_info_list == null;
		},
	},
	created() {
		try {
			messenger.register("edit", this.messenger_onMessage, null, null);
			this.uuid = this.$route.params.uuid;
			if (this.$route.params.query) {
				this.query = this.$route.params.query;
				if (this.query.name !== "") {
					this.edit_query_available_movies(this.query_start_page);
				}
			} else {
				this.query = {
					name: "",
					source_items: [],
					source_values: [],
					provider_items: [],
					provider_values: [],
					category_items: [],
					category_values: [],
					searchtext: "",
				};
			}
			this.edit_query_available_sources();
			// if we edit a quick search, identified by a name given, we instandly do a search

			console.log("Edit loaded");
		} catch (error) {
			console.log("Edit exception", error);
			this.nav2Main();
		}
	},
	methods: {
		nav2Main() {
			router.push({ name: "Home" }); // always goes 'back enough' to Main
		},
		requestPlay(movie_uri) {
			console.log("requestPlay", movie_uri);
			messenger.emit("edit_play_request", {
				uuid: this.uuid,
				query: this.query,
				movie_uri: movie_uri,
			});
			this.nav2Main();
		},
		requestPlayAdd(movie_uri) {
			console.log("requestPlayAdd", movie_uri);
			messenger.emit("edit_play_add_request", {
				uuid: this.uuid,
				query: this.query,
				movie_uri: movie_uri,
			});
		},
		requestRecordAdd(movie_uri) {
			console.log("requestRecordAdd", movie_uri);
			messenger.emit("edit_record_add_request", {
				uuid: this.uuid,
				query: this.query,
				movie_uri: movie_uri,
			});
		},
		messenger_onMessage(type, data) {
			console.log("incoming message to edit", type, data);
			if (type == "edit_query_available_sources_answer") {
				this.query.source_items = data.select_items;
				this.query.source_values = data.select_values;
				this.edit_query_available_providers();
				//this.edit_query_available_categories();
			}
			if (type == "edit_query_available_providers_answer") {
				this.query.provider_items = data.select_items;
				this.query.provider_values = data.select_values;
				this.edit_query_available_categories();
			}
			if (type == "edit_query_available_categories_answer") {
				// in case we have seperate text and values, we need to localise the text first
				data.select_items.forEach((element) => {
					if (element.text) {
						element.text = this.$t(element.text);
					}
				});
				this.query.category_items = data.select_items;
				this.query.category_values = data.select_values;
			}
			if (type == "edit_query_available_movies_answer") {
				this.movie_info_list = data.movie_info_list;
				this.prev_page = data.prev_page;
				this.query_start_page = data.query_start_page;
				this.next_page = data.next_page;
			}
		},
		edit_query_available_sources() {
			console.log("edit_query_available_sources");
			messenger.emit("edit_query_available_sources", {
				select_source_values: this.query.source_values,
			});
		},
		edit_query_available_providers() {
			console.log("edit_query_available_providers");
			messenger.emit("edit_query_available_providers", {
				select_source_values: this.query.source_values,
				select_provider_values: this.query.provider_values,
			});
		},
		edit_query_available_categories() {
			console.log("edit_query_available_categories");
			messenger.emit("edit_query_available_categories", {
				select_source_values: this.query.source_values,
				select_provider_values: this.query.provider_values,
				select_category_values: this.query.category_values,
			});
		},
		edit_query_available_movies(query_start_page) {
			console.log("edit_query_available_movies");
			messenger.emit("edit_query_available_movies", {
				select_source_values: this.query.source_values,
				select_provider_values: this.query.provider_values,
				select_category_values: this.query.category_values,
				select_searchtext: this.query.searchtext,
				query_start_page: query_start_page,
			});
			this.movie_info_list = null;
		},
		localDate(timestamp, locale) {
			return dayjs.unix(timestamp).local().format(locale);
		},
		duration(secondsValue) {
			var totalsecs = parseInt(secondsValue, 10);
			if (!Number.isInteger(totalsecs || totalsecs < 0)) {
				return "";
			}
			var secs = ("0" + totalsecs % 60 ).slice(-2)
			totalsecs = Math.floor(totalsecs / 60)
			var mins = ("0" + totalsecs % 60 ).slice(-2)
			totalsecs = Math.floor(totalsecs / 60)
			var hours = ("0" + totalsecs).slice(-2)
			if (totalsecs < 1) {
				return mins+':'+secs
			} else {
				return hours+':'+mins+':'+secs
			}
		},
	},
};
</script>

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
