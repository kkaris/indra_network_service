<template>
  <div class="container">
    <!-- <pre>{{ networkSearchQuery }}</pre>-->
    <!--
      Todo:
        - Add border for form (use cards?)
        - Organize options according to type of search
        - Implement some basic styling that makes the form readable
        - Make Multi-select prettier (find package):
          + Check out https://github.com/vueform/multiselect, used in
            indra_db/benchmarker/view_app/benchmark.html
          +
        - Add hover or "?" text for help
        - Put checkboxes in row-col setup; Try
          + col-auto class -
            https://getbootstrap.com/docs/5.0/forms/layout/#auto-sizing
          + or row-cols-auto -
            https://getbootstrap.com/docs/5.0/layout/grid/#row-columns
          or horizontal form -
            https://getbootstrap.com/docs/5.0/forms/layout/#horizontal-form
        - See if it's possible to set form inputs to their defaults if the
          field/input is disabled
        - Consider datalists for autocomplete text inputs:
          https://getbootstrap.com/docs/5.0/forms/form-control/#datalists
     -->
    <form class="review-form" @submit.prevent="sendForm">
      <h1>The Network Search Form</h1>
      <h2>Basic Search Options</h2>
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
      <h2>Detailed Search Options</h2>
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
                    <b>Statement Filter</b>
                    <div id="v-model-select-stmts">
                      <select v-model="stmt_filter" multiple>
                        <option
                            v-for="option in stmtFilterOptions"
                            :key="option.value"
                            :selected="stmt_filter"
                            :value="option.value"
                        >{{ option.label }}
                        </option>
                      </select>
                      <br/>
                      <span>Selected: {{ stmt_filter }}</span>
                    </div>
                  </div>
                  <div class="col">
                    <b>Node Namespace</b>
                    <div id="v-model-select-namespace">
                      <select v-model="allowed_ns" multiple>
                        <option
                            v-for="option in nodeNamespaceOptions"
                            :key="option.value"
                            :selected="allowed_ns"
                            :value="option.value"
                        >{{ option.label }}
                        </option>
                      </select>
                      <br/>
                      <span>Selected: {{ allowed_ns }}</span>
                    </div>
                  </div>
                </div>
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
                  <div class="col-md-auto">
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
                    <div id="v-model-select-terminal-ns">
                      <p>Terminal NS</p>
                      <select
                          v-model="terminal_ns"
                          :disabled="isContextSearch || isNotOpenSearch"
                          multiple
                      >
                        <option
                            v-for="option in nodeNamespaceOptions"
                            :key="option.value"
                            :selected="terminal_ns"
                            :value="option.value"
                        >{{ option.label }}
                        </option>
                      </select>
                      <br/>
                      <span>Selected: {{ terminal_ns }}</span>
                    </div>
                  </div>
                  <div class="col">
                    <!-- Disable max per node if weighted or context search -->
                    <BaseInputBS
                        v-model="max_per_node"
                        :disabled="isNotOpenSearch || isContextSearch || isAnyWeighted"
                        :min="1"
                        label="Maximum number of children per node in unweighted breadth first search"
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
                <div class="row">
                  <div class="col">
                    <button
                        :class="{ disabledButton: cannotSubmit }"
                        :disabled="cannotSubmit"
                        class="button btn btn-secondary btn-lg"
                        type="submit"
                    >Submit
                    </button>
                  </div>
                  <div class="col">
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
              </div>
            </div>
          </div>
        </div>
      </div>
    </form>
  </div>
  <ResultArea
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

export default {
  components: {ResultArea, BaseSelectBS, BaseCheckboxBS, BaseInputBS },
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
      sign: "",
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
      format: "html", // This is hardcoded here and is not an option
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
        { label: "FPLX", value: "fplx" },
        { label: "UPPRO", value: "uppro" },
        { label: "HGNC", value: "hgnc" },
        { label: "UP", value: "up" },
        { label: "CHEBI", value: "chebi" },
        { label: "GO", value: "go" },
        { label: "MESH", value: "mesh" },
        { label: "MIRBASE", value: "mirbase" },
        { label: "DOID", value: "doid" },
        { label: "HP", value: "hp" },
        { label: "EFO", value:"efo" },
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
      AxiosMethods.submitForm(this.networkSearchQuery)
      .then(response => {
        console.log('Query resolved!');
        console.log(response);
        this.results = response.data
      })
      .catch(error => {
        console.log(error)
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
