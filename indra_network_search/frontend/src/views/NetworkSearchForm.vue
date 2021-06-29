<template>
  <div class="container">
    <!-- <pre>{{ networkSearchQuery }}</pre>-->
    <!--
      Todo:
        - Add hover or "?" text for help
        - Put checkboxes in row-col setup; Try
          + col-auto class -
            https://getbootstrap.com/docs/5.0/forms/layout/#auto-sizing
          + or row-cols-auto -
            https://getbootstrap.com/docs/5.0/layout/grid/#row-columns
          or horizontal form -
            https://getbootstrap.com/docs/5.0/forms/layout/#horizontal-form
        - See if it's possible to set form inputs to their defaults if the
          field/input is disabled. This could be done by checking
          $attrs.disabled, which will be Boolean if defined, otherwise
          undefined
        - Consider datalists for autocomplete text inputs:
          https://getbootstrap.com/docs/5.0/forms/form-control/#datalists
     -->
    <form class="review-form" @submit.prevent="sendForm">
      <h1 class="text-center">The INDRA Network Search</h1>
      <p class="text-center">
        Read the <a href="https://network.indra.bio/dev/redoc">API Docs</a>
      </p>
      <p class="text-center">
        Read the <a href="https://indra-network-search.readthedocs.io/en/latest/">General Docs</a>
      </p>
      <h2 class="text-center">Basic Search Options</h2>
      <div class="container">
        <div class="row">
          <div class="col">
            <BaseInputBS
                v-model="source"
                label="Source node"
                type="text"
                placeholder="e.g. 'MEK'"
            />
          </div>
          <div class="col">
            <BaseInputBS
                v-model="target"
                label="Target node"
                type="text"
                placeholder="e.g. 'ACE2'"
            />
          </div>
        </div>
      </div>
      <h2 class="text-center">Detailed Search Options</h2>
      <div
          class="accordion"
          :id="accordionID"
      >
        <!-- Accordion 1: General Filter Options -->
        <div class="accordion-item">
          <h3
              class="accordion-header"
              :id="accordionIDObj.accordionHeader1ID"
          >
            <button
                class="accordion-button collapsed"
                type="button"
                data-bs-toggle="collapse"
                :data-bs-target="`#${accordionIDObj.accordionBody1ID}`"
                aria-expanded="false"
                :aria-controls="accordionIDObj.accordionBody1ID"
            >
              <strong>General Filter Options</strong>
            </button>
          </h3>
          <div
              :id="accordionIDObj.accordionBody1ID"
              class="accordion-collapse collapse"
              :aria-labelledby="accordionIDObj.accordionHeader1ID"
          >
            <div class="accordion-body">
              <div class="container">
                <div class="row">
                  <div class="col">
                    <BaseInputBS
                        v-model="hash_blacklist_text"
                        label="Hash Blacklist"
                        type="text"
                    />
                  </div>
                  <div class="col">
                    <BaseInputBS
                        v-model="node_blacklist_text"
                        label="Node Blacklist"
                        type="text"
                    />
                  </div>
                </div>
                <div class="row">
                  <div class="col">
                    <BaseInputBS
                        v-model.number="path_length"
                        :disabled="isAnyWeighted"
                        :max="10"
                        :min="1"
                        label="Path length"
                        type="number"
                    />
                  </div>
                  <div class="col">
                    <BaseSelectBS
                        v-model.number="sign"
                        :options="signOptions"
                        label="Signed Search"
                    />
                  </div>
                </div>
                <div class="row">
                  <div class="col">
                    <BaseInputBS
                        v-model.number="k_shortest"
                        :max="50"
                        :min="1"
                        label="Max Paths"
                        type="number"
                    />
                  </div>
                  <div class="col">
                    <BaseInputBS
                        v-model.number="belief_cutoff"
                        :max="1.0"
                        :min="0.0"
                        :step="0.01"
                        label="Belief Cutoff"
                        type="number"
                    />
                  </div>
                </div>
                <div class="row">
                  <div class="col">
                    <BaseInputBS
                        v-model.number="cull_best_node"
                        :min="1"
                        label="Highest Degree Node Culling Frequency"
                        :title="cullTitle"
                        type="number"
                    />
                  </div>
                  <div class="col">
                    <Multiselect
                        v-model="stmt_filter"
                        mode="tags"
                        placeholder="Allowed Statement Types"
                        title="All types are allowed if no types are selected"
                        :searchable="true"
                        :createTag="false"
                        :options="stmtFilterOptions"
                    />
                    <Multiselect
                        v-model="allowed_ns"
                        mode="tags"
                        placeholder="Allowed Node Namespaces"
                        title="All namespaces are allowed if no namespaces are selected"
                        :searchable="true"
                        :createTag="false"
                        :options="nodeNamespaceOptions"
                    />
                  </div>
                </div>
                <div class="row">
                  <div class="col-6">
                    <BaseCheckboxBS
                        v-model="weighted"
                        label="Weighted search"
                    />
                    <BaseCheckboxBS
                        v-model="curated_db_only"
                        label="Only Database Supported Sources"
                    />
                    <BaseCheckboxBS
                        v-model="fplx_expand"
                        label="Set source/target equivalent to their parents"
                    />
                    <BaseCheckboxBS
                        v-model="two_way"
                        label="Include Reverse Search"
                    />
                    <BaseCheckboxBS
                        v-model="shared_regulators"
                        :disabled="!isNotOpenSearch && !cannotSubmit"
                        label="Include Search for shared regulators of source/target"
                    />
                  </div>
                  <div class="col-6">
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <!-- Accordion 2: Context Search Options -->
        <div class="accordion-item">
          <h3
              class="accordion-header"
              :id="accordionIDObj.accordionHeader2ID"
          >
            <button
                class="accordion-button  collapsed"
                type="button"
                data-bs-toggle="collapse"
                :data-bs-target="`#${accordionIDObj.accordionBody2ID}`"
                aria-expanded="false"
                :aria-controls="accordionIDObj.accordionBody2ID"
            >
              <strong>Context Search Options</strong>
            </button>
          </h3>
          <div
              :id="accordionIDObj.accordionBody2ID"
              class="accordion-collapse collapse"
              :aria-labelledby="accordionIDObj.accordionHeader2ID"
          >
            <div class="accordion-body">
              <div class="row">
                <div class="col">
                  <BaseInputBS
                      v-model="mesh_ids_text"
                      :disabled="weighted"
                      label="Mesh IDs (comma separated)"
                      type="text"
                  />
                </div>
                <div class="col">
                  <BaseInputBS
                      v-model.number="const_c"
                      :disabled="weighted || strict_mesh_id_filtering"
                      :max="100"
                      :min="1"
                      label="Constant C"
                      type="number"
                  />
                </div>
              </div>
              <div class="row">
                <div class="col">
                  <BaseCheckboxBS
                      v-model="strict_mesh_id_filtering"
                      :disabled="weighted"
                      label="Strict Mesh ID filtering"
                  />
                </div>
                <div class="col">
                  <BaseInputBS
                      v-model.number="const_tk"
                      :disabled="weighted || strict_mesh_id_filtering"
                      :max="100"
                      :min="1"
                      label="Constant Tk"
                      type="number"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        <!-- Accordion 3: Open Search Options -->
        <div class="accordion-item">
          <h3
              class="accordion-header"
              :id="accordionIDObj.accordionHeader3ID"
          >
            <button
                class="accordion-button collapsed"
                type="button"
                data-bs-toggle="collapse"
                :data-bs-target="`#${accordionIDObj.accordionBody3ID}`"
                aria-expanded="false"
                :aria-controls="accordionIDObj.accordionBody3ID"
            >
              <strong>Open Search Options</strong>
            </button>
          </h3>
          <div
              :id="accordionIDObj.accordionBody3ID"
              class="accordion-collapse collapse"
              :aria-labelledby="accordionIDObj.accordionHeader3ID"
          >
            <div class="accordion-body">
              <!-- Disable open search options if both source and target are set -->
              <div class="container">
                <div class="row">
                  <div class="col">
                    <!-- Check: is terminal ns applied for strict Dijkstra and/or context search? -->
                    <Multiselect
                        v-model="terminal_ns"
                        mode="tags"
                        placeholder="Terminal Namespaces"
                        title="Select the namespaces for which open searches must end on"
                        :disabled="isContextSearch || isNotOpenSearch"
                        :searchable="true"
                        :createTag="false"
                        :options="nodeNamespaceOptions"
                    />
                  </div>
                  <div class="col">
                    <!-- Disable max per node if weighted or context search -->
                    <BaseInputBS
                        v-model="max_per_node"
                        :disabled="isNotOpenSearch || isContextSearch || isAnyWeighted"
                        :min="1"
                        label="Max children per node"
                        type="number"
                    />
                    <BaseInputBS
                        v-model="depth_limit"
                        :disabled="isNotOpenSearch || isContextSearch || isAnyWeighted"
                        :min="1"
                        label="Depth limit in unweighted search"
                        type="number"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div> <!-- end accordion -->
      <div
          class="row justify-content-center align-middle d-flex align-items-center"
          style="margin-top: 10px">
        <div class="col-2">
          <button
              :class="{ disabledButton: cannotSubmit }"
              :disabled="cannotSubmit || isLoading"
              class="button btn btn-secondary btn-lg"
              type="submit"
          >
            <div v-show="isLoading">
              <span
                  class="spinner-border spinner-border-sm" role="status"
                  aria-hidden="true"
              ></span>
            </div>
            Submit
          </button>
        </div>
        <div class="col-2">
          <BaseInputBS
              v-model.number="user_timeout"
              :max="120"
              :min="2"
              :step="1"
              :style="{ maxWidth: '100px' }"
              label="Timeout"
              type="number"
          />
        </div>
      </div>
    </form>
  </div>
  <ResultArea
      v-if="!emptyResult"
      v-bind="results"
  />
</template>

<script>
import BaseSelectBS from "@/components/Form/BaseSelectBS";
import BaseCheckboxBS from "@/components/Form/BaseCheckboxBS";
import BaseInputBS from "@/components/Form/BaseInputBS";
import AxiosMethods from "@/services/AxiosMethods";
import UniqueID from "@/helpers/BasicHelpers";
import ResultArea from "@/views/ResultArea";
import Multiselect from "@vueform/multiselect"
import sharedHelpers from "@/helpers/sharedHelpers";

export default {
  components: {
    ResultArea, BaseSelectBS, BaseCheckboxBS, BaseInputBS, Multiselect
  },
  data() {
    return {
      source: "",
      target: "",
      stmt_filter: [],
      hash_blacklist_text: "",
      allowed_ns: [],
      node_blacklist_text: "",
      path_length: null,
      depth_limit: 2,
      sign: null,
      weighted: false,
      belief_cutoff: 0.0,
      curated_db_only: false,
      fplx_expand: false,
      k_shortest: 50,
      max_per_node: 5,
      cull_best_node: null,
      mesh_ids_text: "",
      strict_mesh_id_filtering: false,
      const_c: 1,
      const_tk: 10,
      user_timeout: 30,
      two_way: false,
      shared_regulators: false,
      terminal_ns: [],
      isLoading: false,
      format: "html", // This is hardcoded here and is not an option
      cullTitle: "At the specified frequency, the highest degree node will "
          + "be added to the node blacklist and excluded from further "
          + "results for path queries (only applies to breadth first search "
          + "and source-target path searches)",
      signOptions: [
        { label: "+", value: 0 },
        { label: "-", value: 1 },
        { label: "No sign", value: null }
      ],
      stmtFilterOptions: [
        // Idea:Load options from an endpoint that returns all options,
        // perhaps static served via "/data" or on S3? This allows a
        // basemodel to be used
        { label: "Gef", value: "Gef" },
        { label: "Gap", value: "Gap" },
        { label: "Complex", value: "Complex" },
        { label: "Translocation", value: "Translocation" },
        { label: "RegulateAmount", value: "RegulateAmount" },
        { label: "Conversion", value: "Conversion" },
        { label: "AddModification", value: "AddModification" },
        { label: "RemoveModification", value: "RemoveModification" },
        { label: "Phosphorylation", value: "Phosphorylation" },
        { label: "Hydroxylation", value: "Hydroxylation" },
        { label: "Sumoylation", value: "Sumoylation" },
        { label: "Acetylation", value: "Acetylation" },
        { label: "Glycosylation", value: "Glycosylation" },
        { label: "Ribosylation", value: "Ribosylation" },
        { label: "Ubiquitination", value: "Ubiquitination" },
        { label: "Farnesylation", value: "Farnesylation" },
        { label: "Geranylgeranylation", value: "Geranylgeranylation" },
        { label: "Palmitoylation", value: "Palmitoylation" },
        { label: "Myristoylation", value: "Myristoylation" },
        { label: "Methylation", value: "Methylation" },
        { label: "Dephosphorylation", value: "Dephosphorylation" },
        { label: "Dehydroxylation", value: "Dehydroxylation" },
        { label: "Desumoylation", value: "Desumoylation" },
        { label: "Deacetylation", value: "Deacetylation" },
        { label: "Deglycosylation", value: "Deglycosylation" },
        { label: "Deribosylation", value: "Deribosylation" },
        { label: "Deubiquitination", value: "Deubiquitination" },
        { label: "Defarnesylation", value: "Defarnesylation" },
        { label: "Degeranylgeranylation", value: "Degeranylgeranylation" },
        { label: "Depalmitoylation", value: "Depalmitoylation" },
        { label: "Demyristoylation", value: "Demyristoylation" },
        { label: "Demethylation", value: "Demethylation" },
        { label: "Autophosphorylation", value: "Autophosphorylation" },
        { label: "Transphosphorylation", value: "Transphosphorylation" },
        { label: "Inhibition", value: "Inhibition" },
        { label: "Activation", value: "Activation" },
        { label: "GtpActivation", value: "GtpActivation" },
        { label: "Association", value: "Association" },
        { label: "DecreaseAmount", value: "DecreaseAmount" },
        { label: "IncreaseAmount", value: "IncreaseAmount" },
      ],
      nodeNamespaceOptions: [
        { label: "FPLX (Genes/Proteins)", value: "fplx" },
        { label: "UPPRO (Protein Chains)", value: "uppro" },
        { label: "HGNC (Genes/Proteins)", value: "hgnc" },
        { label: "UP (Genes/Proteins)", value: "up" },
        { label: "CHEBI (Small Molecules)", value: "chebi" },
        { label: "GO (Biological Process or Location)", value: "go" },
        { label: "MESH (Biological Process or Disease)", value: "mesh" },
        { label: "MIRBASE (microRNA)", value: "mirbase" },
        { label: "DOID (Diseases)", value: "doid" },
        { label: "HP (Phenotypic Abnormality)", value: "hp" },
        { label: "EFO (Experimental factors)", value:"efo" },
      ],
      // Follows indra_network_search.data_models::Results
      results: {
        query_hash: '',
        time_limit: 30.0,
        timed_out: false,
        hashes: [],
        path_results: {},
        reverse_path_results: {},
        ontology_results: {},
        shared_target_results: {},
        shared_regulators_results: {},
      }
    };
  },
  computed: {
    // putting networkSearchQuery as a computed property makes it
    // automatically update whenever any of the dependencies (i.e. all the
    // options) update. This allows to use the component methods like
    // this.splitTrim() to make an array of comma separated text.
    // This object should conform with
    // indra_network_search.data_model.NetworkSearchQuery
    networkSearchQuery() {
      return {
        source: this.source,
        target: this.target,
        stmt_filter: this.stmt_filter,
        edge_hash_blacklist: this.splitTrim(this.hash_blacklist_text),
        allowed_ns: this.allowed_ns, // Pick from multi-select
        node_blacklist: this.splitTrim(this.node_blacklist_text),
        path_length: this.path_length,
        depth_limit: this.depth_limit,
        sign: this.sign,
        weighted: this.weighted,
        belief_cutoff: this.belief_cutoff,
        curated_db_only: this.curated_db_only,
        fplx_expand: this.fplx_expand,
        k_shortest: this.k_shortest,
        max_per_node: this.max_per_node,
        cull_best_node: this.cull_best_node,
        mesh_ids: this.splitTrim(this.mesh_ids_text),
        strict_mesh_id_filtering: this.strict_mesh_id_filtering,
        const_c: this.const_c,
        const_tk: this.const_tk,
        user_timeout: this.user_timeout,
        two_way: this.two_way,
        shared_regulators: this.shared_regulators,
        terminal_ns: this.terminal_ns, // Pick from multi-select
        format: this.format,
      }
    },
    isContextSearch() {
      return this.mesh_ids_text.length > 0;
    },
    isNotOpenSearch() {
      return this.source.length > 0 && this.target.length > 0;
    },
    cannotSubmit() {
      return this.source.length === 0 && this.target.length === 0;
    },
    isContextWeighted() {
      return this.isContextSearch && !this.strict_mesh_id_filtering;
    },
    isAnyWeighted() {
      return this.isContextWeighted || this.weighted;
    },
    emptyResult() {
      const noPaths = sharedHelpers.isEmptyObject(this.results.path_results);
      const noPathsRev = sharedHelpers.isEmptyObject(
          this.results.reverse_path_results
      );
      const noOnt =
          sharedHelpers.isEmptyObject(this.results.ontology_results) ||
          !(this.results.ontology_results.parents &&
            this.results.ontology_results.parents.length);
      const shrdTarg = sharedHelpers.isEmptyObject(
          this.results.shared_target_results
      );
      const shrdReg = sharedHelpers.isEmptyObject(
          this.results.shared_regulators_results
      );
      return noPaths && noPathsRev && noOnt && shrdTarg && shrdReg
    },
    strUUID() {
      return `form-id-${this.uuid}`
    },
    accordionID() {
      return `accordion-${this.strUUID}`
    },
    accordionIDObj() {
      return {
        accordionHeader1ID: `header1-${this.accordionID}`,
        accordionHeader2ID: `header2-${this.accordionID}`,
        accordionHeader3ID: `header3-${this.accordionID}`,
        accordionBody1ID: `body1-${this.accordionID}`,
        accordionBody2ID: `body2-${this.accordionID}`,
        accordionBody3ID: `body3-${this.accordionID}`,
      }
    },
  },
  methods: {
    sendForm() {
      // Form validation goes here
      if (!this.validateForm()) {
        return false
      }
      this.isLoading = true;
      AxiosMethods.submitForm(this.networkSearchQuery)
      .then(response => {
        console.log('Query resolved!');
        console.log(response);
        this.results = response.data
      })
      .catch(error => {
        console.log(error)
      })
      .then(() => {
        this.isLoading = false;
      })
    },
    splitTrim(inputText) {
      // Splits on comma and trims each item for whitespace, if empty
      // return empty array
      if (inputText) {
        return inputText.split(",").map((e) => {
          return e.trim();
        });
      } else {
        return [];
      }
    },
    validateForm() {
      return true;
      // Here go over all form parts and validate them
    },
  },
  setup() {
    const uuid = UniqueID().getID();
    return {
      uuid
    }
  },
};
</script>
