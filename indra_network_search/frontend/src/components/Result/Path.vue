<template>
  <td class="border-end">
    <Node v-bind="path[0]" />
    <template v-for="(nodeObj, index) in path.slice(1)" :key="index">
      <i class="bi bi-arrow-right"></i>
      <Node v-bind="nodeObj"/>
    </template>
  </td>
  <td>
  <div class="container border rounded-lg">
    <div class="row" v-for="(edge, index) in edge_data" :key="index">
      <Edge v-bind="edge" />
    </div>
  </div>
  </td>
</template>

<script>
import sharedHelpers from "@/helpers/sharedHelpers";
import Node from "@/components/Result/Node";
import Edge from "@/components/Result/Edge";

export default {
  components: {Edge, Node},
  props: {
    // Follows indra_network_search.data_models::Path
    path: {
      type: Array,
      required: true,
      validator: arr => {
        return sharedHelpers.isNodeArray(arr)
      }
    },
    edge_data: {
      type: Array,
      required: true,
      validator: arr => {
        return arr.length > 0;
      }
    }
  },
}
</script>
