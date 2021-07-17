<!-- https://blog.kulturbanause.de/2013/12/css-grid-layout-module/ -->
<template>
<div class="schnipsl-recordcard">
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
				<div id="next">{{ item.movie_info.next_title }}</div>
				<div id="edit">
					<card-menu :item="item"/>
				</div>
				<div id="show">
					<v-btn icon @click="description_show = !description_show">
						<v-icon color="orange darken-1">{{ description_show ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
					</v-btn>

				</div>
				
					<!-- <progress id="viewed" :value="progress(item.current_time,item.movie_info.duration)" max="100">{{progress(item.current_time,item.movie_info.duration)}} %</progress> -->
				<div id="viewed">
					<div :style="{width: progress(item.current_time,item.movie_info.duration)+'%'}"></div>
				</div>
				
				<!-- <div id="description"> -->
					<v-expand-transition>
						<div id="description" v-show="description_show">
							{{item.movie_info.description}}
						</div>
					</v-expand-transition>
				<!-- </div> -->
				
	</div>
</template>
<script>
import CardMenu from "./CardMenu.vue";
export default {
	name: "recordcard",
	components: {
		CardMenu
	},

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
			'localMinutes',
			'progress'],
	methods:{
	}
	
};
</script>

<style scoped>
.schnipsl-recordcard {
  display: grid;
  grid-template-columns: 10px 1fr 1fr 1fr 1fr 40px;
  grid-template-rows: repeat(4, min-content);
  gap: 0px 0px;
	grid-template-areas:  
	"marker name name name provider provider" 
	"marker series series series series share" 
	"marker day time duration . edit" 
	"marker viewed viewed viewed  viewed show" 
	"marker description description description description description" 
  ; 
  background:grey; 
    border-radius: 10px;
  padding: 5px;
  margin-bottom: 10px;
  }

#marker { 
  background:rgb(211, 208, 10); 
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
  text-align:right;
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