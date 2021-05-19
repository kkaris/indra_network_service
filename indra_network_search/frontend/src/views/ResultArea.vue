<template>
  <div class="container border rounded-lg">
    <h1>Results</h1>
    <p>Click on titles to expand results</p>
    <!--Source/Target info???-->
    <!--Ontology Results-->
    <!--Path Results-->
    <!--Reverse Path Results-->
    <!--Shared Targets-->
    <!--Shared Regulators-->
    <h1>Test Space</h1>
    <div class="container border rounded-lg">
      <p>testNode1: <Node v-bind="testNode1" /></p>
    </div>
    <div class="container border rounded-lg">
      <p>testNode2: <Node v-bind="testNode2" /></p>
    </div>
  </div>
</template>

<script>
import sharedHelpers from "@/helpers/sharedHelpers";
import PathResults from "@/components/Result/PathResults";

export default {
  components: {PathResults},
  /* To spread together two objects into another object for usage in a v-bind:
  * v-bind="{...this.testStmt111,
  *          subjNode: this.testNode1,
  *          objNode: this.testNode2}"
  * */
  computed: {
    hasPathRes() {
      return !(sharedHelpers.isEmptyObject(this.path_results))
    },
    hasRevPathRes() {
      return !(sharedHelpers.isEmptyObject(this.reverse_path_results))
    },
    hasOntRes() {
      return !(sharedHelpers.isEmptyObject(this.ontology_results))
    },
    hasSharedTargets() {
      return !(sharedHelpers.isEmptyObject(this.shared_target_results)) &&
          this.shared_target_results.source_data.length &&
          this.shared_target_results.target_data.lenght;
    },
    hasSharedRegs() {
      return !(sharedHelpers.isEmptyObject(this.shared_regulators_results))
    },
  },
  props: {
    // indra_network_search.data_models::Results
    query_hash: {
      // str
      type: String,
      required: true,
    },
    time_limit: {
      // float
      type: Number,
      required: true,
    },
    timed_out: {
      // bool
      type: Boolean,
      required: true
    },
    hashes: {
      // List[str]
      type: Array,
      required: true,
      validator: arr => {
        // Check if array if string
        return arr.every(sharedHelpers.isStr)
      }
    },
    path_results: {
      // Optional[PathResultData] = None
      type: Object,
      default: null
      // Validated in children
    },
    reverse_path_results: {
      // Optional[PathResultData] = None
      type: Object,
      default: null
      // Validated in children
    },
    ontology_results: {
      // Optional[OntologyResults] = None
      type: Object,
      default: null
      // Validated in children
    },
    shared_target_results: {
      // Optional[SharedInteractorsResults] = None
      type: Object,
      default: null
      // Validated in children
    },
    shared_regulators_results: {
      // Optional[SharedInteractorsResults]
      type: Object,
      default: null
      // Validated in children
    },
  }
};
</script>
