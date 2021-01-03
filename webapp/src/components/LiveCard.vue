<!-- https://blog.kulturbanause.de/2013/12/css-grid-layout-module/ -->
<template>
<div class="schnipsl-livecard">
	<div id="marker"></div> 
				<div id="name" @click="nav2Play(item.movie_info.uri)">{{
					item.movie_info.title
				}}</div>
				<div id="series">{{ item.movie_info.category }}</div>
				<div id="provider">{{ item.movie_info.provider }}</div>
				<div id="day">{{
					localDateTime(
						item.movie_info.timestamp,
						$t("locale_date_format")
					)
				}}</div>
				<div id="time">{{
					localDateTime(
						item.movie_info.timestamp,
						$t("locale_time_format")
					)
				}}</div>
				<div id="duration">{{ duration(item.movie_info.duration) }}</div>
				<div id="next"></div>
				<div id="edit"
					><v-btn icon @click="nav2Edit(item.uuid, item.query, item)">
						<v-icon color="grey lighten-1">mdi-pencil</v-icon>
					</v-btn></div
				>
				<div id="share">
					<v-btn icon @click="share(item.uuid)">
						<v-icon color="grey lighten-1">mdi-share-variant</v-icon>
					</v-btn></div
				>
				<div id="record">
					<v-btn
						icon
						v-if="item.movie_info.recordable"
						@click="requestRecordAdd(item.movie_info.uri)"
					>
						<v-icon color="grey lighten-1">mdi-record</v-icon>
					</v-btn>
				</div>
				<div id="show">
					<v-btn icon @click="description_show = !description_show">
						<v-icon color="grey lighten-1">{{ description_show ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
					</v-btn>

				</div>
				
					<!-- <progress id="viewed" :value="progress(item.current_time,item.movie_info.duration)" max="100">{{progress(item.current_time,item.movie_info.duration)}} %</progress> -->
				<div id="viewed">
					<div></div>
				</div>
				
				<div id="description">
					<v-expand-transition>
						<div v-show="description_show">
							{{item.movie_info.description}}
						</div>
					</v-expand-transition>
				</div>
				
	</div>
</template>
<script>
export default {
	name: "livecard",

	props: {
		item: Object
	},
	data () {
		return {
			description_show:false
		}
	},
	inject: ['nav2Edit',
			'nav2Play',
			'requestRecordAdd',
			'share',
			'localDateTime',
			'duration',
			'localMinutes'],
	methods:{
		progress( ) {
			return 70
		},
		progress2( viewed,duration) {
			return viewed*100 / duration
		},

	}
	
};
</script>

<style scoped>
.schnipsl-livecard {
  display: grid;
  grid-template-columns: 10px 1fr 1fr 1fr 1fr 40px;
  grid-template-rows: repeat(5, min-content);
  gap: 0px 0px;
	grid-template-areas:  
	"marker name name name name edit" 
	"marker series series series series share" 
	"marker provider day time duration record" 
	"marker next next next next show" 
	"marker viewed viewed viewed  viewed viewed" 
	"marker description description description description description" 
  ; 
}

#marker { 
  background:rgb(255, 0, 0); 
  grid-area: marker;  
} 
#name { 
  background:gold; 
  grid-area: name;
  font-family: "Atkinson-Hyperlegible", Helvetica, Arial;
  font-size:200%;
  text-align:left;
  padding-left: 5px;
  font-weight: bold;
  
} 
#series { 
  background:lightgreen; 
  grid-area: series;
  font-family: "Atkinson-Hyperlegible", Helvetica, Arial;
  font-size:150%;
  text-align:left;
  padding-left: 5px;
} 
#provider { 
  background:lightblue; 
  grid-area: provider;
  text-align:left;
}
#day { 
  background:lightblue; 
  grid-area: day;
}
#time { 
  background:lightblue; 
  grid-area: time;
}
#duration { 
  background:lightblue; 
  grid-area: duration;
}
#next { 
  background:lightgreen; 
  grid-area: next;
  font-family: "Atkinson-Hyperlegible", Helvetica, Arial;
  font-size:100%;
  text-align:left;
  padding-left: 5px;
} 

#viewed {
  background-color: black;
  border-radius: 13px;
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
  grid-area: edit;
} 
#share { 
  background:grey; 
  grid-area: share;
} 
#record { 
  background:grey; 
  grid-area: record;
} 
#show { 
  background:grey; 
  grid-area: show;
} 
description { 
  background:grey; 
  grid-area: description;
} 


</style>