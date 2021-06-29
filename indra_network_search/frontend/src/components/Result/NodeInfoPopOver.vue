<template>
<!-- Utilizes BootStrap 5's modal component -->
<!-- Button triggered modal -->
<a
    type="button"
    :title="title"
    @click="fillXrefs()"
    class="node-modal"
    data-bs-toggle="modal"
    :data-bs-target="`#${strUUID}`">
  <b>{{ name }}</b>
</a>

<!-- Modal -->
<div class="modal fade"
     :id="strUUID"
     tabindex="-1"
     :aria-labelledby="`label-${strUUID}`"
     aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5
            class="modal-title"
            :id="`label-${strUUID}`"
        >Modal title</h5>
        <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"></button>
      </div>
      <div class="modal-body">
        <table class="table">
          <thead>
            <tr>
              <th>Namespace</th>
              <th>Identifier</th>
              <th>Lookup</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(triple, index) in allRefs"
                :key="`${strUUID}-row${index}`">
              <td v-for="(item, colindex) in triple"
                  :key="`${strUUID}-row${index}-col${colindex}`">{{ item }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="modal-footer">
        Modal footer<br/>
        <button type="button"
                class="btn btn-secondary"
                data-bs-dismiss="modal"
        >Close</button>
      </div>
    </div>
  </div>
</div>
</template>

<script>
import AxiosMethods from "@/services/AxiosMethods";
import UniqueID from "@/helpers/BasicHelpers";

export default {
  // Match the fields of class Node in indra_network_search/data_models.py
  props: {
    name: {
      type: String,
      default: ''
    },
    namespace: {
      type: String,
      required: true
    },
    identifier: {
      type: String,
      required: true
    },
    sign: {
      // Currently unused in this context
      type: Number,
      default: null
    },
    lookup: {
      type: String,
      default: ''
    },
  },
  data() {
    return {
      xrefs: [],
    }
  },
  computed: {
    title() {
      return `Grounded to: ${this.namespace}:${this.identifier}.` +
          'Click for more info';
    },
    allRefs() {
      return [...[[this.namespace, this.identifier, this.lookup]],
              ...this.xrefs]
    },
    strUUID() {
      return `modal-${this.uuid}`
    }
  },
  methods: {
    fillXrefs() {
      if (!this.xrefs.length) {
        AxiosMethods.getXrefs(this.namespace, this.identifier)
            .then(response => {
              this.xrefs = response.data;
            })
            .catch(error => {
              console.log(error)
            })
      }
      else {
        return false;
      }
    }
  },
  setup() {
    const uuid = UniqueID().getID();
    return {
      uuid,
    }
  }
}
</script>
