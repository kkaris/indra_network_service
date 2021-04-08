<template>
  <div class="container">
    <!-- <pre>{{ networkSearchQuery }}</pre>-->
    <form class="review-form" @submit.prevent="sendForm">
      <h1>The Network Search Form</h1>
      <h2>Basic Search Options</h2>
      <div class="container">
        <div class="row">
          <div class="col">
            <BaseInput
              v-model="source"
              label="Source node"
              type="text"
            />
          </div>
          <div class="col">
            <BaseInput
              v-model="target"
              label="Target node"
              type="text"
            />
          </div>
        </div>
      </div>
      <h2>Detailed Search Options</h2>
      <h3>Statement Filter Multi Select</h3>
      <div id="v-model-select-stmts">
        <select v-model="stmt_filter" multiple>
          <option
            v-for="option in stmtFilterOptions"
            :value="option.value"
            :key="option.value"
            :selected="stmt_filter"
          >{{ option.label }}</option>
        </select>
        <br />
        <span>Selected: {{ stmt_filter }}</span>
      </div>
      <h3>Node Namespace</h3>
      <div id="v-model-select-namespace">
        <select v-model="allowed_ns" multiple>
          <option
            v-for="option in nodeNamespaceOptions"
            :value="option.value"
            :key="option.value"
            :selected="allowed_ns"
          >{{ option.label }}</option>
        </select>
        <br/>
        <span>Selected: {{ allowed_ns }}</span>
      </div>
      <h3>Weighted search ({{ weighted }})</h3>
        <BaseCheckbox
          v-model="weighted"
          label="Weighted search"
        />
      <h3>Context Search Options</h3>
      <div>
        <BaseInput
          v-model="mesh_ids_text"
          label="Mesh IDs (comma separated)"
          type="text"
          :disabled="weighted"
        />
        <BaseCheckbox
          v-model="strict_mesh_id_filtering"
          label="Strict Mesh ID filtering"
          :disabled="weighted"
        />
        <br />
        <BaseInput
          v-model.number="const_c"
          label="Constant C"
          type="number"
          :min="1"
          :max="100"
          :disabled="weighted || strict_mesh_id_filtering"
        />
        <BaseInput
          v-model.number="const_tk"
          label="Constant Tk"
          type="number"
          :min="1"
          :max="100"
          :disabled="weighted || strict_mesh_id_filtering"
        />
      </div>
      <h3>Open Search Options</h3>
      <!-- Disable open search options if both source and target are set -->
      <div>
        <!-- Disable max per node if weighted or context search -->
        <BaseInput
          v-model="max_per_node"
          label="Maximum number of children per node in unweighted breadth first search"
          type="number"
          :min="1"
          :disabled="isNotOpenSearch || isContextSearch || isAnyWeighted"
        />
        <!-- Check: is terminal ns applied for strict Dijkstra and/or context search? -->
        <div id="v-model-select-terminal-ns">
          <p>Terminal NS</p>
          <select
            v-model="terminal_ns"
            multiple
            :disabled="isContextSearch || isNotOpenSearch"
          >
            <option
              v-for="option in nodeNamespaceOptions"
              :value="option.value"
              :key="option.value"
              :selected="terminal_ns"
            >{{ option.label }}</option>
          </select>
          <br />
          <span>Selected: {{ terminal_ns }}</span>
        </div>
      </div>
      <br />
      <BaseInput
        v-model="hash_blacklist_text"
        label="Hash Blacklist"
        type="text"
      />
      <BaseInput
        v-model="node_blacklist_text"
        label="Node Blacklist"
        type="text"
      />
      <BaseInput
        v-model.number="path_length"
        label="Path length"
        type="number"
        :min="1"
        :max="10"
        :disabled="isAnyWeighted"
      />
      <BaseInput
        v-model.number="k_shortest"
        label="Max Paths"
        type="number"
        :min="1"
        :max="50"
      />
      <BaseInput
        v-model.number="belief_cutoff"
        label="Belief Cutoff"
        type="number"
        :min="0.0"
        :max="1.0"
        :step="0.01"
      />
      <BaseInput
        v-model.number="user_timeout"
        label="Timeout"
        type="number"
        :min="2"
        :max="120"
        :step="1"
      />
      <h3>Checkboxes</h3>
      <div>
        <BaseCheckbox
          v-model="curated_db_only"
          label="Only Database Supported Sources"
        />
        <BaseCheckbox
          v-model="fplx_expand"
          label="Set source/target as equivalent to their parents"
        />
        <BaseCheckbox
          v-model="two_way"
          label="Include Reverse Search"
        />
        <BaseCheckbox
          v-model="shared_regulators"
          label="Include Search for shared regulators of source/target"
        />
      </div>
      <h3>Signed Search</h3>
      <div>
        <BaseSelect
          :options="signOptions"
          v-model.number="sign"
          label="Sign"
        />
      </div>

      <button
        class="button btn btn-secondary btn-lg"
        :class="{ disabledButton: cannotSubmit }"
        type="submit"
        :disabled="cannotSubmit"
      >Submit</button>
    </form>
  </div>
</template>

<script>
import BaseSelect from "@/components/BaseSelect";
import BaseCheckbox from "@/components/BaseCheckbox";
import BaseInput from "@/components/BaseInput";
import AxiosMethods from "@/services/AxiosMethods";

export default {
  components: { BaseSelect, BaseCheckbox, BaseInput },
  data() {
    return {
      source: "",
      target: "",
      stmt_filter: [],
      hash_blacklist_text: "",
      allowed_ns: [],
      node_blacklist_text: "",
      path_length: null,
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
      ]
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
    }
  },
  methods: {
    sendForm() {
      // Form validation goes here
      if (!this.validateForm()) {
        return false
      }
      AxiosMethods.submitForm(this.networkSearchQuery)
      .then(response => {
        console.log(response)
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
};
</script>
