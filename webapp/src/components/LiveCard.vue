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
						class="mx-4"
						v-if="item.movie_info.recordable"
						@click="requestRecordAdd(item.movie_info.uri)"
					>
						<v-icon size="24px">mdi-record</v-icon>
					</v-btn>
				</div>
				<div id="show">
					<v-btn icon @click="description_show = !description_show">
						<v-icon>{{ description_show ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
					</v-btn>

				</div>
				<div id="viewed">{{ localMinutes(item.current_time) }}</div>
				
				<description>
					<v-expand-transition>
						<div v-show="description_show">
							{{item.movie_info.description}}
						</div>
					</v-expand-transition>
				</description>
				
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
	
};
</script>

<style scoped>
.schnipsl-livecard {
  display: grid;
  grid-template-columns: 10px 1fr 1fr 1fr 1fr max-content;
  grid-template-rows: 1fr 1fr 1fr 1fr 20px;
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
  background:tomato; 
  grid-area: marker;  
} 
#name { 
  background:gold; 
  grid-area: name;
  font-family:verdana;
  font-size:200%;
  text-align:left;
} 
#series { 
  background:lightgreen; 
  grid-area: series;
  font-family:verdana;
  font-size:150%;
  text-align:left;
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
} 
#viewed { 
  background:gold; 
  grid-area: viewed;
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


/* For presentation only, no need to copy the code below */
.grid-container * {
  border: 1px solid red;
  position: relative;
}

.grid-container *:after {
  content:attr(class);
  position: absolute;
  top: 0;
  left: 0;
}

</style>