<template>
  <div class="card text-center">
    <div class="card-header">
      <div class="d-flex justify-content-between">
        <h2>{{ title }}</h2>
        <a
            role="button"
            data-bs-toggle="collapse"
            :href="`#${strUUID}`"
            :aria-expanded="false"
            :aria-controls="strUUID"
        >
          <i title="Click to expand" class="bi-plus-circle fs-2"></i>
        </a>
      </div>
    </div>
    <div class="card-body collapse show" :id="strUUID">
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
import UniqueID from "@/helpers/BasicHelpers";

export default {
  components: {NPathResult},
  props: {
    // Corresponds to indra_network_search/data_models::PathResultData
    // source and target are Node objects
    title: {
      type: String,
      required: true
    },
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
  },
  setup() {
    const uuid = UniqueID().getID();
    return {
      uuid,
    }
  },
  computed: {
    strUUID() {
      return `collapse-${this.uuid}`
    },
  }
}
</script>
