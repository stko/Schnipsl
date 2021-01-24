<template>
	<v-app toolbar footer dark>
		<!-- Provides the application the proper gutter -->
		<v-main>
			<v-container>
				<router-view />
			</v-container>
		</v-main>
		<v-row justify="center">

		</v-row>
		<v-row justify="center">
			<v-dialog v-model="offline_dialog_show" max-width="300px">
			<!--<v-dialog  max-width="300px"> -->
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
			<player/>
		</v-footer>
	</v-app>
</template>

<script>
import Player from "./components/Player.vue";
import messenger from "./messenger";
export default {
	components: {
		Player
	},
	data() {
		return {

			uri: null,
			offline_dialog_show: false,
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
			if (type == "app_user_message") {
				this.user_message = data.message;
				this.snackbar = true;
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
