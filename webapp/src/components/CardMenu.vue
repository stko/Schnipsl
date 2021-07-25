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
						<v-list-item>
							<v-list-item-title>
								<v-btn icon @click="share(item.uuid)">
									<v-icon color="orange darken-1">mdi-share-variant</v-icon>
								</v-btn>
							</v-list-item-title>
						</v-list-item>
						<v-list-item>
							<v-list-item-title>
								<v-btn icon @click="edit_delete_dialog_show = item.uuid">
									<v-icon>mdi-delete</v-icon>
								</v-btn>
							</v-list-item-title>
						</v-list-item>
					</v-list>
		</v-menu>
		<v-dialog v-model="edit_delete_dialog_show" scrollable max-width="300px">
			<v-card>
				<v-card-title>{{ $t("edit_delete_dialog_header") }}</v-card-title>
				<v-divider></v-divider>
				<v-card-actions>
					<v-btn
						color="blue darken-1"
						text
						@click="edit_delete_dialog_show = null"
						>{{ $t("edit_delete_dialog_cancel") }}</v-btn
					>
					<v-btn color="blue darken-1" text @click="edit_delete(edit_delete_dialog_show)">{{
						$t("edit_delete_dialog_select")
					}}</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>
	</div>
</template>
<script>
import messenger from "../messenger";
export default {
	name: "cardmenu",

	props: {
		item: Object
	},
	model: {
	prop: 'list',
	event: 'deleterequest'
},
	data () {
		return {
			description_show:false,
			edit_delete_dialog_show :null
		}
	},
	inject: ['nav2Edit',
			'requestRecordAdd',
			'share'],
	methods:{
		edit_delete(uuid) {
			console.log("requestDelete", uuid);
			this.edit_delete_dialog_show = null;
			messenger.emit("edit_delete_request", {
				uuid: uuid,
			});
		},
	}
	
};
</script>

<style scoped>
</style>