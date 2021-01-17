<!-- https://blog.kulturbanause.de/2013/12/css-grid-layout-module/ -->
<template>
	<div class="schnipsl-player">
		<div id="name">{{ movie_info.title }}</div>
		<div id="series">{{ movie_info.category }}</div>
		<div id="provider">{{ movie_info.provider }}</div>
		<div id="day">{{ localDate(movie_info.timestamp, $t("locale_date_format")) }}</div>
		<div id="time">{{ duration(movie_info.current_time) }}</div>
		<div id="duration">{{ duration(movie_info.duration) }}</div>
		<div id="show">
			<v-btn icon @click="description_show = !description_show">
				<v-icon>{{ description_show ? "mdi-chevron-up" : "mdi-chevron-down" }}</v-icon>
			</v-btn>
		</div>
		<div id="volume">
						<v-slider
							v-model="app_player_pos.volume"
							prepend-icon="mdi-volume-low"
							append-icon="mdi-volume-high"
							@click="player_volume()"
						></v-slider>
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
		<div id="minus10">
			<v-btn icon class="mx-4" @click="player_key('minus10')">
				<v-icon size="24px">mdi-rewind-10</v-icon>
			</v-btn>
		</div>
		<div id="play">
			<v-btn icon class="mx-4" @click="player_key('play')">
				<v-icon>{{
					app_player_pos.play ? "mdi-pause" : "mdi-play"
				}}</v-icon>
			</v-btn>
		</div>
		<div id="plus10">
			<v-btn icon class="mx-4" @click="player_key('plus10')">
				<v-icon size="24px">mdi-fast-forward-10</v-icon>
			</v-btn>
		</div>
		<div id="stop">
			<v-btn icon class="mx-4" @click="player_key('stop')">
				<v-icon size="24px">mdi-stop</v-icon>
			</v-btn>
		</div>
		<div id="bed">
			<v-btn icon class="mx-4" v-if="movie_info.recordable" @click="stop_and_record_dialog_show = true">
				<v-icon size="24px">mdi-bed</v-icon>
			</v-btn>
		</div>
		<div id="position">
						{{ duration(app_player_pos.current_time) }}
						<v-slider v-model="sliderPosition" append-icon="mdi-timer"></v-slider>
						{{ duration(movie_info.duration - app_player_pos.current_time) }}
		</div>
		<v-expand-transition>
			<div id="description" v-show="description_show">
				{{movie_info.description}}
			</div>
		</v-expand-transition>
	</div>
</template>
<script>
import messenger from "../messenger";
export default {
	name: "player",

	props: {
		app_player_pos: Object,
		movie_info: Object
	},
	data () {
		return {
			description_show:false,
		}
	},
	inject: ['localDate',
			'duration'],
	methods:{
		player_key(id) {
			console.log("Send key");
			messenger.emit("player_key", { keyid: id });
		},
		player_volume() {
			console.log("Send volume");
			messenger.emit("player_volume", {
				timer_vol: this.app_player_pos.volume,
			});
		},
	},
	computed: {
		sliderPosition: {
			// getter
			get: function () {
				if (
					this.app_player_pos.current_time >= 0 &&
					this.app_player_pos.duration > 0
				) {
					return parseInt(
						(this.app_player_pos.current_time * 100) /
							this.app_player_pos.duration
					);
				} else {
					return NaN;
				}
			},
			// setter
			set: function (newValue) {
				console.log("Send timer by setter");
				this.app_player_pos.current_time = newValue;
				messenger.emit("player_time", {
					timer_pos: this.app_player_pos.current_time,
				});
			},
		},
	},
};
</script>

<style scoped>
.schnipsl-player {
  display: grid;
  grid-template-columns: repeat(7,13vw);
  grid-template-rows: repeat(7, min-content);
  gap: 0px 0px;
	grid-template-areas:  
	"name name name name name name name" 
	"series series series series series series series" 
	"provider provider day time duration duration show" 
	"volume volume volume volume volume volume volume" 
	"device prev minus10 play plus10 stop bed" 
	"position position position position position position position" 
	"description description description description description description description" 
  ; 
  background:grey; 
    border-radius: 10px;
  padding: 5px;
  margin-bottom: 10px;
  max-width: 98vw;
  }

#marker { 
  background:rgb(255, 0, 0); 
  grid-area: marker;  
  border-radius: 5px;
} 
#name { 
  background:grey; 
  color: white;
  grid-area: name;
  font-family: "Atkinson-Hyperlegible", Helvetica, Arial;
  font-size:200%;
  line-height: 100%;
  text-align:left;
  padding-left: 5px;
  font-weight: bold;
  
} 
#series { 
  background:grey; 
  color: white;
  grid-area: series;
  font-family: "Atkinson-Hyperlegible", Helvetica, Arial;
  font-size:150%;
  text-align:left;
  padding-left: 5px;
} 
#provider { 
  background:grey; 
  color:lightgray; 
  font-weight: bold;
  grid-area: provider;
  text-align:left;
  padding-left: 5px;
}
#day { 
  background:grey; 
  color:lightgray; 
  font-weight: bold;
  grid-area: day;
}
#time { 
  background:grey; 
  color:lightgray; 
  font-weight: bold;
  grid-area: time;
}
#duration { 
  background:grey; 
  color:lightgray; 
  font-weight: bold;
  grid-area: duration;
}
#next { 
  background:grey; 
  color: white; 
  grid-area: next;
  font-family: "Atkinson-Hyperlegible", Helvetica, Arial;
  font-size:100%;
  text-align:left;
  padding-left: 5px;
} 

#volume {
  background:grey; 
  /*border-radius: 13px;*/
  /* (height of inner div) / 2 + padding */
  padding: 3px;
  grid-area: volume;
}

#position {
  background:grey; 
  /*border-radius: 13px;*/
  /* (height of inner div) / 2 + padding */
  padding: 3px;
  grid-area: position;
}

#viewed {
  background:grey; 
  /*border-radius: 13px;*/
  /* (height of inner div) / 2 + padding */
  padding: 3px;
  grid-area: viewed;
}

#viewed>div {
  background-color: orange;
  width: 40%;
  /* Adjust with JavaScript */
  height: 20px;
  border-radius: 10px;
}


#edit { 
  background:grey; 
  color: white; 
  grid-area: edit;
} 
#share { 
  background:grey; 
  color: white; 
  grid-area: share;
} 
#record { 
  background:grey; 
  color: white; 
  grid-area: record;
} 
#show { 
  background:grey; 
  color: white;
  grid-area: show;
} 
#description { 
  background:grey; 
  color: white;
  grid-area: description;
} 


</style>