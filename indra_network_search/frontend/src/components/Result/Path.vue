<template>
  <td class="border-end align-middle">
    <NodeModal v-bind="path[0]" />
    <template v-for="(nodeObj, index) in path.slice(1)" :key="index">
      <i class="bi bi-arrow-right"></i>
      <NodeModal v-bind="nodeObj"/>
    </template>
  </td>
  <td>
    <div class="container">
      <template v-for="(edge, index) in edge_data" :key="index">
        <div class="row">
          <Edge v-bind="edge" />
        </div>
      </template>
    </div>
  </td>
</template>

<script>
import sharedHelpers from "@/helpers/sharedHelpers";
import NodeModal from "@/components/Result/NodeModal";
import Edge from "@/components/Result/Edge";

export default {
  components: {Edge, NodeModal},
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
