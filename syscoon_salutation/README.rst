Syscoon Salutation
==================

This Module allows to use a gender based salutation in Emails and Reports.

Usage in Emails:
----------------
<p>
    % if object.partner_id.title:
        ${object.partner_id.partner_salutation},<br></p><p>
    % endif
    % if not object.partner_id.title:
        Sehr geehrte Damen und Herren,<br></p><p>
    % endif
</p>

Usage in Reports:
-----------------
<p>
    <t t-if="o.partner_id.title">
        <span t-field="o.partner_id.partner_salutation",
    </t>
    <t t-if="not object.partner_id.title">
        Sehr geehrte Damen und Herren,
    </t>
</p>