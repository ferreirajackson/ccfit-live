<!DOCTYPE html>
{% extends 'ccfit_app/base.html' %}
{% block body_block %}
<h1>THATS THE YPUR BOOKINGS PAGE</h1>
<a href="{% url 'ccfit_app:index' %}">SOMETHING HERE</a>


<table>
    <tr>
        <td>Date</td>
        <td>user</td>
        <td>session</td>
        <td>Class</td>
    </tr>

    {% for key, values in data.items %}
    <tr>
        <td>{{key}}</td>
        {% for v in values %}
        <td>{{v}}</td>
        {% endfor %}
    </tr>
    {% endfor %}
</table>
{% endblock %}
