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
        <table class="table">
          <thead>
            <tr>
              <th>{{ `Shared ${sharedNode}` }}</th>
              <th>Support</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(stArr, index) in coOrderedEdges" :key="index">
              <tr>
                <td class="align-middle">
                  <!-- If shared targets -->
                  <template v-if="downstream"><NodeModal v-bind="stArr[0].edge[1]"/></template>
                  <!-- If shared regulators -->
                  <template v-else><NodeModal v-bind="stArr[0].edge[0]"/></template>
                </td>
                <td>
                  <InteractorRow
                      :source-edge-data="stArr[0]"
                      :target-edge-data="stArr[1]"
                  />
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import NodeModal from "@/components/Result/NodeModal";
import sharedHelpers from "@/helpers/sharedHelpers";
import UniqueID from "@/helpers/BasicHelpers";
import InteractorRow from "@/components/Result/InteractorRow";

export default {
  components: {InteractorRow, NodeModal},
  props: {
    // Follows indra_network_search.data_models::SharedInteractorsResults
    source_data: {
      type: Array,
      required: true,
      validator: arr => {
        return arr.every(sharedHelpers.isEdgeData)
      }
    },
    target_data: {
      type: Array,
      required: true,
      validator: arr => {
        return arr.every(sharedHelpers.isEdgeData)
      }
    },
    downstream: {
      type: Boolean,
      required: true
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
    coOrderedEdges() {
      return sharedHelpers.zipEqualArrays(this.source_data, this.target_data)
    },
    title() {
      return this.downstream ? 'Shared Targets' : 'Shared Regulators'
    },
    sharedNode() {
      return this.downstream ? 'target' : 'regulator'
    }
  }
}
</script>
