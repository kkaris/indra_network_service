<template>
  <div class="container">
    <h1>Results</h1>
    <p>Click on titles to expand results</p>
    <!--Source/Target info???-->
    <!--Ontology Results-->
    <CommonParents
        v-if="hasOntRes"
        v-bind="ontology_results"
    />
    <!--Path Results-->
    <PathResults
        v-if="hasPathRes"
        v-bind="{...path_results, title: 'Path Results'}"
    />
    <!--Reverse Path Results-->
    <PathResults
        v-if="hasRevPathRes"
        v-bind="{ ...reverse_path_results, title: 'Reverse Path Results' }"
    />
    <!--Shared Targets-->
    <SharedInteractors
        v-if="hasSharedTargets"
        v-bind="shared_target_results"
    />
    <!--Shared Regulators-->
    <SharedInteractors
        v-if="hasSharedRegs"
        v-bind="shared_regulators_results"
    />
  </div>
</template>

<script>
import sharedHelpers from "@/helpers/sharedHelpers";
import PathResults from "@/components/Result/PathResults";
import CommonParents from "@/components/Result/CommonParents";
import SharedInteractors from "@/components/Result/SharedInteractors";

export default {
  components: {SharedInteractors, CommonParents, PathResults},
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
      return !sharedHelpers.isEmptyObject(this.ontology_results) &&
          this.ontology_results.parents &&
          this.ontology_results.parents.length > 0
    },
    hasSharedTargets() {
      return !(sharedHelpers.isEmptyObject(this.shared_target_results)) &&
          this.shared_target_results.source_data.length &&
          this.shared_target_results.target_data.length;
    },
    hasSharedRegs() {
      return !(sharedHelpers.isEmptyObject(this.shared_regulators_results)) &&
          this.shared_regulators_results.source_data.length &&
          this.shared_regulators_results.target_data.length;
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
