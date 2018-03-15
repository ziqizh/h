'use strict';

const Controller = require('../base/controller');
const { setElementState } = require('../util/dom');

/**
 * Controller for items in a list of fields.
 */
class ListInputItemController extends Controller {
  constructor(element) {
    super(element);

    const hasError = !!this.refs.errorList;
    element.addEventListener('input', () => {
      this.setState({ error: false });
    });

    this.setState({ error: hasError });
  }

  update() {
    if (this.refs.errorList) {
      setElementState(this.refs.errorList, { hidden: !this.state.error });
    }
  }
}

module.exports = ListInputItemController;
