<template>
  <div class="container">
    <h1>Results</h1>
    <p>Click on titles to expand results</p>
    <div
        class="accordion"
        :id="accordionID"
    >
      <!--Source/Target info???-->
      <!--Ontology Results-->
      <div v-if="hasOntRes" class="accordion-item">
        <h2 class="accordion-header" :id="accordionIDObj.accHeadOnt">
          <button
              class="accordion-button"
              type="button"
              data-bs-toggle="collapse"
              :data-bs-target="`#${accordionIDObj.accBodyOnt}`"
              aria-expanded="false"
              :aria-controls="accordionIDObj.accBodyOnt"
          >
            Path Results
          </button>
        </h2>
        <div
            class="accordion-collapse collapse show"
            :id="accordionIDObj.accBodyOnt"
            :aria-labelledby="accordionIDObj.accHeadOnt"
        >
          <div class="accordion-body">
            <CommonParents v-bind="ontology_results" />
          </div>
        </div>
      </div>
    </div>
      <!--Path Results-->
<!--      <div class="accordion-item">-->
        <PathResults
          v-if="hasPathRes"
          v-bind="{...path_results, title: 'Path Results'}"
      />
<!--      </div>-->
      <!--Reverse Path Results-->
<!--      <div class="accordion-item">-->
        <PathResults
          v-if="hasRevPathRes"
          v-bind="{ ...reverse_path_results, title: 'Reverse Path Results' }"
      />
<!--      </div>-->
      <!--Shared Targets-->
<!--      <div class="accordion-item">-->
        <SharedInteractors
          v-if="hasSharedTargets"
          v-bind="shared_target_results"
      />
<!--      </div>-->
      <!--Shared Regulators-->
<!--      <div class="accordion-item">-->
        <SharedInteractors
          v-if="hasSharedRegs"
          v-bind="shared_regulators_results"
      />
<!--      </div>-->
<!--    </div> accordion end-->
  </div>
</template>

<script>
import sharedHelpers from "@/helpers/sharedHelpers";
import PathResults from "@/components/Result/PathResults";
import CommonParents from "@/components/Result/CommonParents";
import SharedInteractors from "@/components/Result/SharedInteractors";
import UniqueID from "@/helpers/BasicHelpers";

export default {
  components: {SharedInteractors, CommonParents, PathResults},
  /* To spread together two objects into another object for usage in a v-bind:
  * v-bind="{...this.testStmt111,
  *          subjNode: this.testNode1,
  *          objNode: this.testNode2}"
  * */
  computed: {
    accordionID() {
      return `accordion-${this.uuid}`
    },
    accordionIDObj() {
      return {
        accHeadOnt: `headerOnt-${this.accordionID}`,
        accBodyOnt: `headerOnt-${this.accordionID}`,
        accHeadPath: `headerPath-${this.accordionID}`,
        accBodyPath: `headerPath-${this.accordionID}`,
        accHeadRevPath: `headerRevPath-${this.accordionID}`,
        accBodyRevPath: `headerRevPath-${this.accordionID}`,
        accHeadTar: `headerTar-${this.accordionID}`,
        accBodyTar: `headerTar-${this.accordionID}`,
        accHeadReg: `headerReg-${this.accordionID}`,
        accBodyReg: `headerReg-${this.accordionID}`,
      }
    },
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
  },
  setup() {
    const uuid = UniqueID().getID();
    return {
      uuid
    }
  }
};
</script>
