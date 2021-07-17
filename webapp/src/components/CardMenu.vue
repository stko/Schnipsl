<!-- https://blog.kulturbanause.de/2013/12/css-grid-layout-module/ -->
<template>
	<div class="schnipsl-cardmenu">
		<v-menu bottom left	rounded="pill">
					<template v-slot:activator="{ on, attrs }">
						<v-btn
						dark
						icon
						v-bind="attrs"
						v-on="on"
						>
						<v-icon>mdi-dots-vertical</v-icon>
						</v-btn>
					</template>
		
					<v-list color="grey darken+2">
						<v-list-item>
							<v-list-item-title>
								<v-btn icon @click="nav2Edit(item.uuid, item.query)">
									<v-icon color="orange darken-1">mdi-pencil</v-icon>
								</v-btn>
							</v-list-item-title>
						</v-list-item>
						<v-list-item>
							<v-list-item-title>
								<v-btn icon @click="share(item.uuid)">
									<v-icon color="orange darken-1">mdi-share-variant</v-icon>
								</v-btn>
							</v-list-item-title>
						</v-list-item>
						<v-list-item v-if="item.movie_info.recordable">
							<v-list-item-title>
								<v-btn
									icon
									@click="requestRecordAdd(item.movie_info.uri)"
								>
									<v-icon color="red darken-1">mdi-record</v-icon>
								</v-btn>
							</v-list-item-title>
						</v-list-item>
					</v-list>
		</v-menu>
	</div>
</template>
<script>
export default {
	name: "cardmenu",

	props: {
		item: Object
	},
	data () {
		return {
			description_show:false
		}
	},
	inject: ['nav2Edit',
			'requestRecordAdd',
			'share'],
	methods:{
	}
	
};
</script>

<style scoped>
</style>