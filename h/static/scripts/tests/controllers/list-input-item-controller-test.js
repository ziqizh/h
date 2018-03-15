'use strict';

const ListInputItemController = require('../../controllers/list-input-item-controller');

const { setupComponent } = require('./util');

describe('ListInputItemController', () => {
  const template = hasError => `
    <li class="js-list-input-item">
      <input type="text" name="some-text-input">
      ${hasError ? '<ul class="is-error" data-ref="errorList"></ul>'
                 : ''}
    </li>
  `.trim();

  it('adds "is-hidden" class to "errorList" part when input occurs', () => {
    const ctrl = setupComponent(document, template(true), ListInputItemController);
    const input = ctrl.element.querySelector('input');

    input.dispatchEvent(new Event('input', { bubbles: true }));

    assert.equal(ctrl.refs.errorList.classList.contains('is-hidden'), true);
  });

  it('handles inputs in list items with no error', () => {
    const ctrl = setupComponent(document, template(false), ListInputItemController);
    const input = ctrl.element.querySelector('input');

    input.dispatchEvent(new Event('input'));
  });
});
