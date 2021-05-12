<template>
  <div class="card text-center">
    <h2 class="card-header">Path Results</h2>
    <div class="card-body">
      <div class="container">
        <template v-for="(pathArray, nodeCount, index) in paths" :key="index">
          <div class="row">
            <NPathResult
              :source="source"
              :target="target"
              :path-array="pathArray"
              :path-node-count="nodeCount"
            />
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import sharedHelpers from "@/helpers/sharedHelpers";
import NPathResult from "@/components/Result/NPathResult";

export default {
  components: {NPathResult},
  props: {
    // Corresponds to indra_network_search/data_models::PathResultData
    // source and target are Node objects
    source: {
      type: Object,
      default: null,
      validator: obj => {
        return sharedHelpers.isOptionalNode(obj)
      }
    },
    target: {
      type: Object,
      default: null,
      validator: obj => {
        return sharedHelpers.isOptionalNode(obj)
      }
    },
    paths: {
      // {<int>: [Path]}
      type: Object,
      required: true
      // ToDo:
      //  - validate that keys are ints
      //  - that the listed objects in the Arrays are Path objects
      //  - that the keys correspond to node count in the list Paths in paths
    }
  }
}
</script>
