<!-- https://blog.kulturbanause.de/2013/12/css-grid-layout-module/ -->
<template>
<div class="schnipsl-quicksearchcard">
	<div id="marker"></div> 
				<div id="name" @click="nav2Edit(item.uuid, item.query)">{{
					item.movie_info.title
				}}</div>
				<div id="share">
					<v-btn icon @click="share(item.uuid)">
						<v-icon color="orange darken-1">mdi-share-variant</v-icon>
					</v-btn></div
				>
	</div>
</template>
<script>
export default {
	name: "quicksearchcard",

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
.schnipsl-quicksearchcard {
  display: grid;
  grid-template-columns: 10px  1fr 40px;
  grid-template-rows: repeat(1, min-content);
  gap: 0px 0px;
	grid-template-areas:  
	"marker name  share" 
  ; 
  background:grey; 
    border-radius: 10px;
  padding: 5px;
  margin-bottom: 10px;
  }

#marker { 
  background:rgb(5, 37, 219); 
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

#share { 
  background:grey; 
  color: white; 
  grid-area: share;
} 

</style>