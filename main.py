from flask import Flask, render_template, redirect
import asyncio

app = Flask(__name__)

@app.errorhandler(404)
async def page_not_found(e):
    return redirect('/welcome')


@app.route('/welcome')
async def welcome():
    return render_template('Landing page.html')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.ensure_future(app.run(debug=True)))