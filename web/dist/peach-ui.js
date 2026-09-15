import { esc as e, icon as t, requestErrorMessage as n, siteMarkUrl as r } from "/js/core.js";
import { MEDIA_SOURCE_ICONS as i, attachOverlayScrollbar as a, checkboxHtml as o, emptyStateHtml as s, fieldsetTitle as c, loadingDotsHtml as l, moveGlidePane as u, noteHtml as d, projectBannerHtml as f, selectFieldHtml as p, selectOptionIconHtml as m, setActionBusy as h, wireAnchoredMenu as g, wireCollapse as _, wireSelectField as v } from "/js/ui-components.js";
//#region node_modules/preact/dist/preact.module.js
var y, b, x, S, C, w, T, E, D, O, k, A, j, ee, te = {}, M = [], ne = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, N = Array.isArray;
function P(e, t) {
	for (var n in t) e[n] = t[n];
	return e;
}
function re(e) {
	e && e.parentNode && e.parentNode.removeChild(e);
}
function ie(e, t, n) {
	var r, i, a, o = {};
	for (a in t) a == "key" ? r = t[a] : a == "ref" ? i = t[a] : o[a] = t[a];
	if (arguments.length > 2 && (o.children = arguments.length > 3 ? y.call(arguments, 2) : n), typeof e == "function" && e.defaultProps != null) for (a in e.defaultProps) o[a] === void 0 && (o[a] = e.defaultProps[a]);
	return ae(e, o, r, i, null);
}
function ae(e, t, n, r, i) {
	var a = {
		type: e,
		props: t,
		key: n,
		ref: r,
		__k: null,
		__: null,
		__b: 0,
		__e: null,
		__c: null,
		constructor: void 0,
		__v: i ?? ++x,
		__i: -1,
		__u: 0
	};
	return i == null && b.vnode != null && b.vnode(a), a;
}
function F(e) {
	return e.children;
}
function oe(e, t) {
	this.props = e, this.context = t;
}
function I(e, t) {
	if (t == null) return e.__ ? I(e.__, e.__i + 1) : null;
	for (var n; t < e.__k.length; t++) if ((n = e.__k[t]) != null && n.__e != null) return n.__e;
	return typeof e.type == "function" ? I(e) : null;
}
function se(e) {
	if (e.__P && e.__d) {
		var t = e.__v, n = t.__e, r = [], i = [], a = P({}, t);
		a.__v = t.__v + 1, b.vnode && b.vnode(a), ve(e.__P, a, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, r, n ?? I(t), !!(32 & t.__u), i), a.__v = t.__v, a.__.__k[a.__i] = a, be(r, a, i), t.__e = t.__ = null, a.__e != n && ce(a);
	}
}
function ce(e) {
	if ((e = e.__) != null && e.__c != null) return e.__e = e.__c.base = null, e.__k.some(function(t) {
		if (t != null && t.__e != null) return e.__e = e.__c.base = t.__e;
	}), ce(e);
}
function le(e) {
	(!e.__d && (e.__d = !0) && S.push(e) && !ue.__r++ || C != b.debounceRendering) && ((C = b.debounceRendering) || w)(ue);
}
function ue() {
	try {
		for (var e, t = 1; S.length;) S.length > t && S.sort(T), e = S.shift(), t = S.length, se(e);
	} finally {
		S.length = ue.__r = 0;
	}
}
function de(e, t, n, r, i, a, o, s, c, l, u) {
	var d, f, p, m, h, g, _ = r && r.__k || M, v = t.length;
	for (c = fe(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || te, p.__i = d, g = ve(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && Ce(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = pe(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
	return n.__e = h, c;
}
function fe(e, t, n, r, i) {
	var a, o, s, c, l, u = n.length, d = u, f = 0;
	for (e.__k = Array(i), a = 0; a < i; a++) (o = t[a]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[a] = ae(null, o, null, null, null) : N(o) ? o = e.__k[a] = ae(F, { children: o }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[a] = ae(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[a] = o, c = a + f, o.__ = e, o.__b = e.__b + 1, s = null, (l = o.__i = me(o, n, c, d)) != -1 && (d--, (s = n[l]) && (s.__u |= 2)), s == null || s.__v == null ? (l == -1 && (i > u ? f-- : i < u && f++), typeof o.type != "function" && (o.__u |= 4)) : l != c && (l == c - 1 ? f-- : l == c + 1 ? f++ : (l > c ? f-- : f++, o.__u |= 4))) : e.__k[a] = null;
	if (d) for (a = 0; a < u; a++) (s = n[a]) != null && !(2 & s.__u) && (s.__e == r && (r = I(s)), we(s, s));
	return r;
}
function pe(e, t, n) {
	var r, i;
	if (typeof e.type == "function") {
		for (r = e.__k, i = 0; r && i < r.length; i++) r[i] && (r[i].__ = e, t = pe(r[i], t, n));
		return t;
	}
	e.__e != t && (t && e.type && !t.parentNode && (t = I(e)), t = n.insertBefore(e.__e, t || null));
	do
		t &&= t.nextSibling;
	while (t != null && t.nodeType == 8);
	return t;
}
function me(e, t, n, r) {
	var i, a, o, s = e.key, c = e.type, l = t[n], u = l != null && !(2 & l.__u);
	if (l === null && s == null || u && s == l.key && c == l.type) return n;
	if (r > +!!u) {
		for (i = n - 1, a = n + 1; i >= 0 || a < t.length;) if ((l = t[o = i >= 0 ? i-- : a++]) != null && !(2 & l.__u) && s == l.key && c == l.type) return o;
	}
	return -1;
}
function he(e, t, n) {
	t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || ne.test(t) ? n : n + "px";
}
function ge(e, t, n, r, i) {
	var a, o;
	n: if (t == "style") {
		if (typeof n == "string") e.style.cssText = n;
		else {
			if (typeof r == "string" && (e.style.cssText = r = ""), r) for (t in r) n && t in n || he(e.style, t, "");
			if (n) for (t in n) r && n[t] == r[t] || he(e.style, t, n[t]);
		}
	} else if (t[0] == "o" && t[1] == "n") a = t != (t = t.replace(k, "$1")), o = t.toLowerCase(), t = o in e || t == "onFocusOut" || t == "onFocusIn" ? o.slice(2) : t.slice(2), e.l ||= {}, e.l[t + a] = n, n ? r ? n[O] = r[O] : (n[O] = A, e.addEventListener(t, a ? ee : j, a)) : e.removeEventListener(t, a ? ee : j, a);
	else {
		if (i == "http://www.w3.org/2000/svg") t = t.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
		else if (t != "width" && t != "height" && t != "href" && t != "list" && t != "form" && t != "tabIndex" && t != "download" && t != "rowSpan" && t != "colSpan" && t != "role" && t != "popover" && t in e) try {
			e[t] = n ?? "";
			break n;
		} catch {}
		typeof n == "function" || (n == null || !1 === n && t[4] != "-" ? e.removeAttribute(t) : e.setAttribute(t, t == "popover" && n == 1 ? "" : n));
	}
}
function _e(e) {
	return function(t) {
		if (this.l) {
			var n = this.l[t.type + e];
			if (t[D] == null) t[D] = A++;
			else if (t[D] < n[O]) return;
			return n(b.event ? b.event(t) : t);
		}
	};
}
function ve(e, t, n, r, i, a, o, s, c, l) {
	var u, d, f, p, m, h, g, _, v, y, x, S, C, w, T, E, D = t.type;
	if (t.constructor !== void 0) return null;
	128 & n.__u && (c = !!(32 & n.__u), a = [s = t.__e = n.__e]), (u = b.__b) && u(t);
	n: if (typeof D == "function") {
		d = o.length;
		try {
			if (v = t.props, y = D.prototype && D.prototype.render, x = (u = D.contextType) && r[u.__c], S = u ? x ? x.props.value : u.__ : r, n.__c ? _ = (f = t.__c = n.__c).__ = f.__E : (y ? t.__c = f = new D(v, S) : (t.__c = f = new oe(v, S), f.constructor = D, f.render = Te), x && x.sub(f), f.state || (f.state = {}), f.__n = r, p = f.__d = !0, f.__h = [], f._sb = []), y && f.__s == null && (f.__s = f.state), y && D.getDerivedStateFromProps != null && (f.__s == f.state && (f.__s = P({}, f.__s)), P(f.__s, D.getDerivedStateFromProps(v, f.__s))), m = f.props, h = f.state, f.__v = t, p) y && D.getDerivedStateFromProps == null && f.componentWillMount != null && f.componentWillMount(), y && f.componentDidMount != null && f.__h.push(f.componentDidMount);
			else {
				if (y && D.getDerivedStateFromProps == null && v !== m && f.componentWillReceiveProps != null && f.componentWillReceiveProps(v, S), t.__v == n.__v || !f.__e && f.shouldComponentUpdate != null && !1 === f.shouldComponentUpdate(v, f.__s, S)) {
					t.__v != n.__v && (f.props = v, f.state = f.__s, f.__d = !1), t.__e = n.__e, t.__k = n.__k, t.__k.some(function(e) {
						e && (e.__ = t);
					}), M.push.apply(f.__h, f._sb), f._sb = [], f.__h.length && o.push(f), s = I(n);
					break n;
				}
				f.componentWillUpdate != null && f.componentWillUpdate(v, f.__s, S), y && f.componentDidUpdate != null && f.__h.push(function() {
					f.componentDidUpdate(m, h, g);
				});
			}
			if (f.context = S, f.props = v, f.__P = e, f.__e = !1, C = b.__r, w = 0, y) f.state = f.__s, f.__d = !1, C && C(t), u = f.render(f.props, f.state, f.context), M.push.apply(f.__h, f._sb), f._sb = [];
			else do
				f.__d = !1, C && C(t), u = f.render(f.props, f.state, f.context), f.state = f.__s;
			while (f.__d && ++w < 25);
			f.state = f.__s, f.getChildContext != null && (r = P(P({}, r), f.getChildContext())), y && !p && f.getSnapshotBeforeUpdate != null && (g = f.getSnapshotBeforeUpdate(m, h)), T = u != null && u.type === F && u.key == null ? xe(u.props.children) : u, s = de(e, N(T) ? T : [T], t, n, r, i, a, o, s, c, l), f.base = t.__e, t.__u &= -161, f.__h.length && o.push(f), _ && (f.__E = f.__ = null);
		} catch (e) {
			if (o.length = d, t.__v = null, c || a != null) {
				if (e.then) {
					for (t.__u |= c ? 160 : 128; s && s.nodeType == 8 && s.nextSibling;) s = s.nextSibling;
					a != null && (a[a.indexOf(s)] = null), t.__e = s;
				} else if (a != null) for (E = a.length; E--;) re(a[E]);
			} else t.__e = n.__e;
			t.__k ??= n.__k || [], e.then || ye(t), b.__e(e, t, n);
		}
	} else a == null && t.__v == n.__v ? (t.__k = n.__k, t.__e = n.__e) : s = t.__e = Se(n.__e, t, n, r, i, a, o, c, l);
	return (u = b.diffed) && u(t), 128 & t.__u ? void 0 : s;
}
function ye(e) {
	e && (e.__c && (e.__c.__e = !0), e.__k && e.__k.some(ye));
}
function be(e, t, n) {
	for (var r = 0; r < n.length; r++) Ce(n[r], n[++r], n[++r]);
	b.__c && b.__c(t, e), e.some(function(t) {
		try {
			e = t.__h, t.__h = [], e.some(function(e) {
				e.call(t);
			});
		} catch (e) {
			b.__e(e, t.__v);
		}
	});
}
function xe(e) {
	return typeof e != "object" || !e || e.__b > 0 ? e : N(e) ? e.map(xe) : e.constructor === void 0 ? P({}, e) : null;
}
function Se(e, t, n, r, i, a, o, s, c) {
	var l, u, d, f, p, m, h, g = n.props || te, _ = t.props, v = t.type;
	if (v == "svg" ? i = "http://www.w3.org/2000/svg" : v == "math" ? i = "http://www.w3.org/1998/Math/MathML" : i ||= "http://www.w3.org/1999/xhtml", a != null) {
		for (l = 0; l < a.length; l++) if ((p = a[l]) && "setAttribute" in p == !!v && (v ? p.localName == v : p.nodeType == 3)) {
			e = p, a[l] = null;
			break;
		}
	}
	if (e == null) {
		if (v == null) return document.createTextNode(_);
		e = document.createElementNS(i, v, _.is && _), s &&= (b.__m && b.__m(t, a), !1), a = null;
	}
	if (v == null) g === _ || s && e.data == _ || (e.data = _);
	else {
		if (a = v == "textarea" && _.defaultValue != null ? null : a && y.call(e.childNodes), !s && a != null) for (g = {}, l = 0; l < e.attributes.length; l++) g[(p = e.attributes[l]).name] = p.value;
		for (l in g) p = g[l], l == "dangerouslySetInnerHTML" ? d = p : l == "children" || l in _ || l == "value" && "defaultValue" in _ || l == "checked" && "defaultChecked" in _ || ge(e, l, null, p, i);
		for (l in _) p = _[l], l == "children" ? f = p : l == "dangerouslySetInnerHTML" ? u = p : l == "value" ? m = p : l == "checked" ? h = p : s && typeof p != "function" || g[l] === p || ge(e, l, p, g[l], i);
		if (u) s || d && (u.__html == d.__html || u.__html == e.innerHTML) || (e.innerHTML = u.__html), t.__k = [];
		else if (d && (e.innerHTML = ""), de(t.type == "template" ? e.content : e, N(f) ? f : [f], t, n, r, v == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, a, o, a ? a[0] : n.__k && I(n, 0), s, c), a != null) for (l = a.length; l--;) re(a[l]);
		s && v != "textarea" || (l = "value", v == "progress" && m == null ? e.removeAttribute("value") : m != null && (m !== e[l] || v == "progress" && !m || v == "option" && m != g[l]) && ge(e, l, m, g[l], i), l = "checked", h != null && h != e[l] && ge(e, l, h, g[l], i));
	}
	return e;
}
function Ce(e, t, n) {
	try {
		if (typeof e == "function") {
			var r = typeof e.__u == "function";
			r && e.__u(), r && t == null || (e.__u = e(t));
		} else e.current = t;
	} catch (e) {
		b.__e(e, n);
	}
}
function we(e, t, n) {
	var r, i;
	if (b.unmount && b.unmount(e), (r = e.ref) && (r.current && r.current != e.__e || Ce(r, null, t)), (r = e.__c) != null) {
		if (r.componentWillUnmount) try {
			r.componentWillUnmount();
		} catch (e) {
			b.__e(e, t);
		}
		r.base = r.__P = r.__n = null;
	}
	if (r = e.__k) for (i = 0; i < r.length; i++) r[i] && we(r[i], t, n || typeof e.type != "function");
	n || re(e.__e), e.__c = e.__ = e.__e = void 0;
}
function Te(e, t, n) {
	return this.constructor(e, n);
}
function Ee(e, t, n) {
	var r, i, a, o;
	t == document && (t = document.documentElement), b.__ && b.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, a = [], o = [], ve(t, e = (!r && n || t).__k = ie(F, null, [e]), i || te, te, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? y.call(t.childNodes) : null, a, !r && n ? n : i ? i.__e : t.firstChild, r, o), be(a, e, o), e.props.children = null;
}
y = M.slice, b = { __e: function(e, t, n, r) {
	for (var i, a, o; t = t.__;) if ((i = t.__c) && !i.__) try {
		if ((a = i.constructor) && a.getDerivedStateFromError != null && (i.setState(a.getDerivedStateFromError(e)), o = i.__d), i.componentDidCatch != null && (i.componentDidCatch(e, r || {}), o = i.__d), o) return i.__E = i;
	} catch (t) {
		e = t;
	}
	throw e;
} }, x = 0, oe.prototype.setState = function(e, t) {
	var n = this.__s != null && this.__s != this.state ? this.__s : this.__s = P({}, this.state);
	typeof e == "function" && (e = e(P({}, n), this.props)), e && P(n, e), e != null && this.__v && (t && this._sb.push(t), le(this));
}, oe.prototype.forceUpdate = function(e) {
	this.__v && (this.__e = !0, e && this.__h.push(e), le(this));
}, oe.prototype.render = F, S = [], w = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, T = function(e, t) {
	return e.__v.__b - t.__v.__b;
}, ue.__r = 0, E = Math.random().toString(8), D = "__d" + E, O = "__a" + E, k = /(PointerCapture)$|Capture$/i, A = 0, j = _e(!1), ee = _e(!0);
//#endregion
//#region src/sort-preferences.ts
function De(e, t, n) {
	return e === "seed" ? "" : e === t && n === "asc" ? "asc" : "desc";
}
//#endregion
//#region src/number-setting.ts
var Oe = {
	loginDaysSetting: {
		min: 1,
		max: 365,
		unit: "天",
		fallback: 30
	},
	batchSizeSetting: {
		min: 1,
		max: 200,
		unit: "个",
		fallback: 60
	},
	hoverDelaySetting: {
		min: 1,
		max: 60,
		unit: "秒",
		optional: !0,
		fallback: 5
	},
	seekSecondsSetting: {
		min: 1,
		max: 300,
		unit: "秒",
		fallback: 10
	},
	relatedLimitSetting: {
		min: 1,
		max: 60,
		unit: "个",
		optional: !0,
		fallback: 20
	},
	searchHistoryLimitSetting: {
		min: 1,
		max: 50,
		unit: "条",
		optional: !0,
		fallback: 10
	},
	followScheduleSetting: {
		min: 15,
		max: 10080,
		unit: "分钟",
		optional: !0,
		fallback: 60
	}
};
function ke(e, t, n, r) {
	return Number.isInteger(e) && e >= t && e <= n ? e : r;
}
function Ae(e, t, n) {
	let r = e.querySelector("input[type=number]"), i = e.querySelector("[role=switch]"), a = e.querySelector(".board-number-fields");
	r && (r.disabled = n, t !== null && t > 0 && (r.value = String(t))), i && (i.disabled = n, t !== null && (i.checked = t > 0)), a && t !== null && (a.hidden = t === 0);
}
function je(e, t, n, r, i) {
	let a = Oe[t];
	if (!a) return !1;
	let { min: o, max: s, unit: c, optional: l, fallback: u } = a, d = `peach.number.${t}`, f = ke(Number(localStorage.getItem(d)), o, s, r > 0 ? r : u), p = document.createElement("div");
	p.className = "board-optional-number";
	let m = document.createElement("div");
	m.className = "board-number-fields", m.hidden = !!l && r === 0;
	let h = document.createElement("div");
	h.className = "board-number-control";
	let g = document.createElement("input");
	g.type = "number", g.className = "geist-input", g.min = String(o), g.max = String(s), g.step = "1", g.value = String(r > 0 ? r : f), g.setAttribute("aria-label", n);
	let _ = document.createElement("span");
	_.textContent = c, _.setAttribute("aria-hidden", "true");
	let v = document.createElement("small");
	v.id = `${t}-error`, v.className = "board-number-error", v.setAttribute("role", "status"), v.hidden = !0, g.setAttribute("aria-describedby", v.id), h.append(g, _), m.append(h, v), p.append(m), e.replaceChildren(p);
	let y = () => {
		g.removeAttribute("aria-invalid"), v.hidden = !0, v.textContent = "";
	}, b = () => {
		if (!g.value || !g.checkValidity()) {
			g.setAttribute("aria-invalid", "true"), v.textContent = `请输入 ${o}–${s} 的整数（${c}）`, v.hidden = !1;
			return;
		}
		y(), f = Number(g.value), localStorage.setItem(d, String(f)), i(g.value);
	};
	if (g.addEventListener("change", b), g.addEventListener("keydown", (e) => {
		e.key === "Enter" && (e.preventDefault(), b());
	}), g.addEventListener("input", () => {
		g.value && g.checkValidity() && y();
	}), l) {
		let e = document.createElement("input");
		e.type = "checkbox", e.className = "ptoggle", e.setAttribute("role", "switch"), e.setAttribute("aria-label", `启用${n}`), e.checked = r > 0, e.onchange = () => {
			y(), m.hidden = !e.checked, e.checked ? (g.value = String(f), b()) : (g.value && g.checkValidity() && (f = Number(g.value)), localStorage.setItem(d, String(f)), i("0"));
		}, p.prepend(e);
	}
	return !0;
}
//#endregion
//#region src/board-metrics.ts
var L = (e) => String(e ?? "").replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]);
function Me(e, t, n, r = "chart-no-axes-combined") {
	return `<span class="board-stat-label"><span class="board-stat-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><use href="#i-${/^[a-z0-9-]+$/.test(r) ? r : "database"}"/></svg></span>${L(e)}</span><b class="board-stat-value">${L(t)}</b><small class="board-stat-footer">${L(n || "当前记录")}</small>`;
}
function Ne(e, t, n) {
	if (!Number.isFinite(n) || n <= 0) return "";
	let r = Math.max(0, Math.min(n, Number.isFinite(t) ? t : 0)), i = r / n * 100;
	return `<div class="board-job-progress" role="progressbar" aria-label="${L(e)}" aria-valuemin="0" aria-valuemax="${n}" aria-valuenow="${r}"><svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true"><circle class="board-job-track" cx="18" cy="18" r="15"/><circle class="board-job-fill" cx="18" cy="18" r="15" pathLength="100" stroke-dasharray="${i} ${100 - i}" transform="rotate(-90 18 18)"/></svg><span>${L(e)}<small>${Math.round(i)}%</small></span></div>`;
}
function Pe(e, t) {
	let n = e.filter((e) => Number.isFinite(e.score) && e.score > 0), r = n.reduce((e, t) => e + t.score, 0);
	if (!r) return "";
	let i = 0, a = n.map((e, t) => {
		let n = e.score / r * 100, a = `<circle cx="100" cy="100" r="72" pathLength="100" fill="none" stroke="var(--chart-${t % 4})" stroke-width="22" stroke-dasharray="${n} ${100 - n}" stroke-dashoffset="${-i}"><title>${L(e.name)}：${e.score.toLocaleString()}</title></circle>`;
		return i += n, a;
	}).join("");
	return `<svg class="board-distribution" viewBox="0 0 200 200" role="img" aria-label="${L(t)}"><g transform="rotate(-90 100 100)">${a}</g><text x="100" y="100" text-anchor="middle" dominant-baseline="middle">${L(t)}</text></svg>`;
}
function Fe(e, t) {
	let n = e.filter((e) => Number.isFinite(e.score) && e.score > 0).slice().sort((e, t) => t.score - e.score).slice(0, 8);
	if (!n.length) return "";
	let r = n[0].score, i = n.map((e) => `<li><span class="board-rank-fill" style="width:${(e.score / r * 100).toFixed(2)}%"></span><span>${L(e.name)}</span><b>${e.score.toLocaleString()}</b></li>`).join("");
	return `<ol class="board-ranked-chart" aria-label="${L(t)}">${i}</ol>`;
}
function Ie(e, t) {
	let n = e.filter((e) => Number.isFinite(e.score) && e.score > 0).slice().sort((e, t) => t.score - e.score).slice(0, 6);
	if (n.length < 3) return "";
	let r = Math.max(...n.map((e) => e.score)), i = n.length, a = (e, t) => {
		let n = e / i * Math.PI * 2 - Math.PI / 2;
		return [160 + Math.cos(n) * t, 140 + Math.sin(n) * t];
	}, o = (e) => n.map((t, n) => a(n, e(n)).map((e) => e.toFixed(2)).join(",")).join(" "), s = [
		25,
		50,
		75,
		100
	].map((e) => `<polygon points="${o(() => e)}" class="board-radar-grid"/>`).join(""), c = n.map((e, t) => {
		let [n, r] = a(t, 116);
		return `<text x="${n}" y="${r}" text-anchor="${n < 145 ? "end" : n > 175 ? "start" : "middle"}">${L(e.name)}</text>`;
	}).join("");
	return `<svg class="board-radar" viewBox="0 0 320 280" role="img" aria-label="${L(t)}"><title>${L(n.map((e) => `${e.name} ${e.score}`).join("，"))}</title>${s}<polygon points="${o((e) => n[e].score / r * 100)}" class="board-radar-value"/>${c}</svg>`;
}
//#endregion
//#region node_modules/preact/hooks/dist/hooks.module.js
var R, z, Le, Re, ze = 0, Be = [], B = b, Ve = B.__b, He = B.__r, Ue = B.diffed, We = B.__c, Ge = B.unmount, Ke = B.__;
function qe(e, t) {
	B.__h && B.__h(z, e, ze || t), ze = 0;
	var n = z.__H || (z.__H = {
		__: [],
		__h: []
	});
	return e >= n.__.length && n.__.push({}), n.__[e];
}
function V(e) {
	return ze = 1, Je(rt, e);
}
function Je(e, t, n) {
	var r = qe(R++, 2);
	if (r.t = e, !r.__c && (r.__ = [n ? n(t) : rt(void 0, t), function(e) {
		var t = r.__N ? r.__N[0] : r.__[0], n = r.t(t, e);
		t !== n && (r.__N = [n, r.__[1]], r.__c.setState({}));
	}], r.__c = z, !z.__f)) {
		var i = function(e, t, n) {
			if (!r.__c.__H) return !0;
			var i = !1, o = r.__c.props !== e;
			if (r.__c.__H.__.some(function(e) {
				if (e.__N) {
					i = !0;
					var t = e.__[0];
					e.__ = e.__N, e.__N = void 0, t !== e.__[0] && (o = !0);
				}
			}), a) {
				var s = a.call(this, e, t, n);
				return i ? s || o : s;
			}
			return !i || o;
		};
		z.__f = !0;
		var a = z.shouldComponentUpdate, o = z.componentWillUpdate;
		z.componentWillUpdate = function(e, t, n) {
			if (this.__e) {
				var r = a;
				a = void 0, i(e, t, n), a = r;
			}
			o && o.call(this, e, t, n);
		}, z.shouldComponentUpdate = i;
	}
	return r.__N || r.__;
}
function H(e, t) {
	var n = qe(R++, 3);
	!B.__s && nt(n.__H, t) && (n.__ = e, n.u = t, z.__H.__h.push(n));
}
function Ye(e, t) {
	var n = qe(R++, 4);
	!B.__s && nt(n.__H, t) && (n.__ = e, n.u = t, z.__h.push(n));
}
function U(e) {
	return ze = 5, Xe(function() {
		return { current: e };
	}, []);
}
function Xe(e, t) {
	var n = qe(R++, 7);
	return nt(n.__H, t) && (n.__ = e(), n.__H = t, n.__h = e), n.__;
}
function Ze() {
	for (var e; e = Be.shift();) {
		var t = e.__H;
		if (e.__P && t) try {
			t.__h.some(et), t.__h.some(tt), t.__h = [];
		} catch (n) {
			t.__h = [], B.__e(n, e.__v);
		}
	}
}
B.__b = function(e) {
	z = null, Ve && Ve(e);
}, B.__ = function(e, t) {
	e && t.__k && t.__k.__m && (e.__m = t.__k.__m), Ke && Ke(e, t);
}, B.__r = function(e) {
	He && He(e), R = 0;
	var t = (z = e.__c).__H;
	t && (Le === z ? (t.__h = [], z.__h = [], t.__.some(function(e) {
		e.__N && (e.__ = e.__N), e.u = e.__N = void 0;
	})) : (t.__h.some(et), t.__h.some(tt), t.__h = [], R = 0)), Le = z;
}, B.diffed = function(e) {
	Ue && Ue(e);
	var t = e.__c;
	t && t.__H && (t.__H.__h.length && (Be.push(t) !== 1 && Re === B.requestAnimationFrame || ((Re = B.requestAnimationFrame) || $e)(Ze)), t.__H.__.some(function(e) {
		e.u &&= (e.__H = e.u, void 0);
	})), Le = z = null;
}, B.__c = function(e, t) {
	t.some(function(e) {
		try {
			e.__h.some(et), e.__h = e.__h.filter(function(e) {
				return !e.__ || tt(e);
			});
		} catch (n) {
			t.some(function(e) {
				e.__h &&= [];
			}), t = [], B.__e(n, e.__v);
		}
	}), We && We(e, t);
}, B.unmount = function(e) {
	Ge && Ge(e);
	var t, n = e.__c;
	n && n.__H && (n.__H.__.some(function(e) {
		try {
			et(e);
		} catch (e) {
			t = e;
		}
	}), n.__H = void 0, t && B.__e(t, n.__v));
};
var Qe = typeof requestAnimationFrame == "function";
function $e(e) {
	var t, n = function() {
		clearTimeout(r), Qe && cancelAnimationFrame(t), setTimeout(e);
	}, r = setTimeout(n, 35);
	Qe && (t = requestAnimationFrame(n));
}
function et(e) {
	var t = z, n = e.__c;
	typeof n == "function" && (e.__c = void 0, n()), z = t;
}
function tt(e) {
	var t = z;
	e.__c = e.__(), z = t;
}
function nt(e, t) {
	return !e || e.length !== t.length || t.some(function(t, n) {
		return t !== e[n];
	});
}
function rt(e, t) {
	return typeof t == "function" ? t(e) : t;
}
//#endregion
//#region src/api.ts
var it = class extends Error {
	status;
	body;
	constructor(e, t, r = null) {
		super(n(e, t)), this.name = "ApiError", this.status = t, this.body = r;
	}
}, at = (e) => {
	if (!e || typeof e != "object") return "";
	let t = e;
	for (let e of [
		"message",
		"detail",
		"error"
	]) {
		let n = t[e];
		if (typeof n == "string" && n) return n;
	}
	return "";
}, W = (e) => n(e);
async function G(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new it(at(r) || `请求失败（${n.status}）`, n.status);
	return r;
}
async function K(e, t, n = "POST", r) {
	let i = await fetch(e, {
		method: n,
		...r ? { signal: r } : {},
		headers: {
			Accept: "application/json",
			"Content-Type": "application/json"
		},
		credentials: "same-origin",
		body: JSON.stringify(t)
	}), a = null;
	try {
		a = await i.json();
	} catch {}
	if (!i.ok) throw new it(at(a) || `请求失败（${i.status}）`, i.status, a);
	return a;
}
//#endregion
//#region src/jobs.ts
function ot(e, t = 0, n = 0) {
	return n > 0 ? Ne(e, t, n) : l(e);
}
async function st(e) {
	let t = e.pause || ((e) => new Promise((t) => setTimeout(t, e))), n = 0;
	for (; e.active();) {
		let r;
		try {
			r = await e.read(AbortSignal.timeout(15e3));
		} catch (r) {
			if (!e.active()) return;
			n++, e.disconnected(r), await t(Math.min(2e3 * 2 ** Math.min(n, 4), 3e4));
			continue;
		}
		if (!e.active() || (n = 0, e.render(r), e.once) || !e.keepWatching && r.status !== "running") return;
		await t(2e3);
	}
}
function ct(e) {
	let t = e.note || ((e) => d(e, {
		label: "任务状态",
		variant: "error"
	})), n = e.loading || l, r = e.progress || ((e, t, n) => ot(n || `已处理 ${e} / ${t}`, e, t)), i = e.container || ((e) => `<section class="followtask" data-geist-fieldset aria-label="任务进度"><div class="geist-fieldset-content">${e}</div></section>`), a = document.createElement("div");
	e.host.hidden = !0, a.dataset.followJob = "", a.setAttribute("aria-live", "polite"), e.host.prepend(a);
	let o = e.storageKey || "peach-follow-job", s = sessionStorage.getItem(o) || void 0, c = !1;
	st({
		read: e.read,
		active: () => !c && e.active() && a.isConnected,
		keepWatching: e.watchIdle !== !1,
		render: (l) => {
			let u = l.status === "running";
			if (e.host.hidden = !u, e.busy(u), u) {
				s = l.job_id, s && sessionStorage.setItem(o, s);
				let t = l.current, c = (t?.attempt || 1) > 1 ? ` · 第 ${t?.attempt}/${t?.max_attempts} 次尝试${t?.retry_in ? `，${t.retry_in} 秒后重试` : ""}` : "", u = (l.message || (e.title ? e.title + (l.total ? `：已完成 ${l.checked || 0}/${l.total}` : "") : "") || (l.total ? `${l.older ? "抓取历史" : "检查更新"}：已完成 ${l.checked || 0}/${l.total} 个来源` : "正在准备检查任务…")) + (t ? ` · ${t.label || t.provider || ""}${c}` : ""), d = (l.total || 0) > 0 ? r(l.checked || 0, l.total, u) : n(u);
				a.innerHTML = i(d);
			} else if (s && s === l.job_id) s = void 0, c = !0, e.host.hidden = l.status !== "failed", sessionStorage.removeItem(o), a.innerHTML = l.status === "failed" ? t(l.error || "检查失败") : "", e.complete(l);
			else {
				if (s && l.status === "idle") {
					e.host.hidden = !1, a.innerHTML = t("任务状态已失效，请重新发起任务"), sessionStorage.removeItem(o), c = !0;
					return;
				}
				a.innerHTML = "";
			}
		},
		disconnected: () => {
			e.host.hidden = !1, a.innerHTML = t("暂时无法读取进度，正在重新连接…");
		}
	});
}
//#endregion
//#region node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var lt = 0;
Array.isArray;
function q(e, t, n, r, i, a) {
	t ||= {};
	var o, s, c = t;
	if ("ref" in c) for (s in c = {}, t) s == "ref" ? o = t[s] : c[s] = t[s];
	var l = {
		type: e,
		props: c,
		key: n,
		ref: o,
		__k: null,
		__: null,
		__b: 0,
		__e: null,
		__c: null,
		constructor: void 0,
		__v: --lt,
		__i: -1,
		__u: 0,
		__source: i,
		__self: a
	};
	if (typeof e == "function" && (o = e.defaultProps)) for (s in o) c[s] === void 0 && (c[s] = o[s]);
	return b.vnode && b.vnode(l), l;
}
//#endregion
//#region src/link-button.tsx
function ut({ href: e, children: t }) {
	return /* @__PURE__ */ q("a", {
		class: "board-link-button",
		href: e,
		children: [/* @__PURE__ */ q("span", { children: t }), /* @__PURE__ */ q("svg", {
			viewBox: "0 0 24 24",
			"aria-hidden": "true",
			children: /* @__PURE__ */ q("use", { href: "#i-arrow-up" })
		})]
	});
}
//#endregion
//#region src/split-action.tsx
function dt({ id: e, label: t, actions: n, busy: r }) {
	let i = U(null), a = U();
	Ye(() => {
		let e = i.current;
		return a.current = g(e, e.querySelector(".splittoggle"), e.querySelector("[role=menu]")), () => a.current?.setOpen(!1);
	}, []), Ye(() => {
		i.current?.querySelectorAll("button").forEach((e) => h(e, r)), r && a.current?.setOpen(!1);
	}, [r]);
	let o = (e) => /* @__PURE__ */ q("svg", {
		viewBox: "0 0 24 24",
		"aria-hidden": "true",
		children: /* @__PURE__ */ q("use", { href: `#i-${e}` })
	}), s = (e) => {
		r || (a.current?.setOpen(!1), e.run());
	};
	return /* @__PURE__ */ q("div", {
		ref: i,
		class: "splitbutton board-button-group primary",
		onClickCapture: (e) => {
			r && (e.preventDefault(), e.stopPropagation());
		},
		onKeyDown: (e) => {
			let t = Array.from(i.current.querySelectorAll("[role=menuitem]"));
			if (e.key === "ArrowDown" || e.key === "ArrowUp") {
				if (e.preventDefault(), r) return;
				a.current?.setOpen(!0);
				let n = t.indexOf(document.activeElement);
				t[n < 0 ? e.key === "ArrowDown" ? 0 : t.length - 1 : (n + (e.key === "ArrowDown" ? 1 : t.length - 1)) % t.length]?.focus();
			}
			e.key === "Tab" && a.current?.setOpen(!1);
		},
		children: [
			/* @__PURE__ */ q("button", {
				type: "button",
				class: "splitmain geist-button primary",
				onClick: () => s(n[0]),
				children: [o(n[0].icon), n[0].label]
			}),
			/* @__PURE__ */ q("button", {
				type: "button",
				class: "splittoggle geist-button primary",
				"aria-label": t,
				"aria-haspopup": "menu",
				"aria-expanded": "false",
				"aria-controls": e,
				children: o("chevron-down")
			}),
			/* @__PURE__ */ q("div", {
				class: "popmenu cardmenupanel",
				id: e,
				role: "menu",
				hidden: !0,
				children: n.map((e) => /* @__PURE__ */ q("button", {
					type: "button",
					role: "menuitem",
					onClick: () => s(e),
					children: [o(e.icon), /* @__PURE__ */ q("span", { children: e.label })]
				}, e.label))
			})
		]
	});
}
//#endregion
//#region src/islands/library-processing.tsx
var ft = (e, t) => G("/api/library-processing", t), pt = {
	reading_local: "读取本地资料",
	querying_metadata: "查询外部资料",
	fetching_cover: "采集缺失封面",
	writing_candidates: "保存资料候选"
}, mt = {
	querying_metadata: "没有资料",
	fetching_cover: "没有封面"
};
function ht(e) {
	let t = Object.entries(e).filter(([e, t]) => mt[e] && t > 0).map(([e, t]) => `${mt[e]} ${t} 部`);
	return t.length ? `外部来源${t.join("、")}，7 天内不再问。` : "";
}
function gt(e) {
	let t = pt[e.current_action || ""] || e.stage || "正在处理", n = e.waited_seconds ? ` · 已等待 ${e.waited_seconds} 秒` : "";
	return e.current_asset_name ? `当前：${e.current_asset_name} · ${t}${n}` : t + n;
}
var _t = "peach.library-processing.announced", vt = 120;
function yt(e, t, n) {
	if (e.status !== "complete") return;
	let r = !!e.job_id && !!e.completed_at && Date.now() / 1e3 - e.completed_at < vt;
	if (!(!n && !r)) {
		try {
			if (e.job_id && localStorage.getItem(_t) === e.job_id) return;
			e.job_id && localStorage.setItem(_t, e.job_id);
		} catch {}
		t(`扫描与资料采集已完成：识别 ${e.identified || 0} 个番号，整理 ${e.candidates || 0} 组资料候选`);
	}
}
function bt({ data: e, error: t, toast: n, onComplete: r, mode: i, monitor: a, preview: o }) {
	let [s, l] = V(e || { status: "idle" }), [u, p] = V(t), [m, h] = V(!1), [g, v] = V(!1), y = U(new AbortController()), b = U(0), x = U(s.status), S = U(null);
	H(() => {
		S.current && _(S.current, ".geist-note-details", "library-issues");
	}, [s, u]);
	let C = m || s.status === "running";
	async function w() {
		let e = ++b.current;
		await st({
			read: (e) => G("/api/library-processing", e),
			active: () => !y.current.signal.aborted && b.current === e,
			keepWatching: i === "notice" || !!a,
			render: (e) => {
				l(e), p("");
				let t = e.status === "complete" && x.current === "running";
				t && i !== "notice" && v(!0), (t || i === "notice") && yt(e, n, t), x.current === "running" && (e.status === "complete" || e.status === "failed") && r?.(), x.current = e.status;
			},
			disconnected: () => p("连接中断，正在重新读取处理进度")
		});
	}
	H(() => (!o && (s.status === "running" || i === "notice" || a) && w(), () => y.current.abort()), []);
	async function T(e) {
		if (!(C || o)) {
			h(!0), p(""), v(!1);
			try {
				let t = await K("/api/library-processing", e, "POST", y.current.signal);
				if (y.current.signal.aborted) return;
				x.current = t.status, l(t), h(!1), await w();
			} catch (e) {
				y.current.signal.aborted || (p(W(e)), h(!1));
			}
		}
	}
	let E = () => void T({}), D = () => {
		!s.job_id || !s.retryable_asset_ids?.length || T({
			job_id: s.job_id,
			retry: s.retryable_asset_ids
		});
	};
	if (i === "notice") {
		if (!u && s.status !== "running" && s.status !== "failed") return null;
		let e = u || (s.status === "failed" ? "扫描与资料采集未完成" : gt(s) + (s.total ? ` · ${s.checked || 0} / ${s.total}` : ""));
		return /* @__PURE__ */ q("div", { dangerouslySetInnerHTML: { __html: f(e, {
			variant: s.status === "failed" ? "error" : u || s.stalled ? "warning" : "gray",
			href: "/data-cleanup#libraryProcessing",
			label: u || s.status === "failed" ? "查看并处理" : "查看进度",
			value: s.checked || 0,
			...s.status === "running" && s.total !== void 0 ? { max: s.total } : {}
		}) } });
	}
	let O = s.issue_preview || [], k = ht(s.notes || {}), A = s.status === "failed" && !!s.retryable_asset_ids?.length, j = O.length ? {
		label: s.issues_truncated ? `问题清单：共 ${s.issue_count || 0} 项，展开查看前 ${O.length} 项` : `问题清单：共 ${s.issue_count || 0} 项`,
		items: O.map((e) => ({
			label: e.title || (e.asset_id ? `视频 ${e.asset_id}` : "媒体来源"),
			href: e.asset_id ? `/item/${e.asset_id}` : "",
			note: e.message,
			hint: e.path || ""
		})),
		footnote: s.issues_log ? `完整记录：${s.issues_log}` : ""
	} : null;
	return /* @__PURE__ */ q(F, { children: [/* @__PURE__ */ q("section", {
		class: "cleanupfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "cleanupScrapingTitle",
		children: [/* @__PURE__ */ q("div", {
			class: "geist-fieldset-content library-processing",
			children: [
				/* @__PURE__ */ q("div", { dangerouslySetInnerHTML: { __html: c("cleanupScrapingTitle", "扫描与采集") } }),
				/* @__PURE__ */ q("p", { children: "扫描媒体文件夹，导入已有资料，采集缺失信息。两段也可以分开跑：新盘刚接上时先只扫描，几万个文件登记完就能用；采集被网络拖住时只重跑采集，不必再扫一遍磁盘。" }),
				s.status === "running" && /* @__PURE__ */ q("div", {
					"aria-live": "polite",
					dangerouslySetInnerHTML: { __html: ot(s.total ? `${gt(s)} · ${s.checked || 0} / ${s.total} 个视频` : gt(s), s.checked, s.total) }
				})
			]
		}), /* @__PURE__ */ q("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [
				/* @__PURE__ */ q(ut, {
					href: "/scraping",
					children: "来源和凭证"
				}),
				!!s.candidates && /* @__PURE__ */ q(ut, {
					href: "/review",
					children: "复核资料"
				}),
				(s.status !== "failed" || !A) && /* @__PURE__ */ q(dt, {
					id: "libraryProcessingMenu",
					label: "更多扫描与采集方式",
					busy: C,
					actions: [
						{
							label: "扫描并补全资料",
							icon: "database",
							run: E
						},
						{
							label: "只扫描",
							icon: "hard-drive",
							run: () => void T({ stage: "scan" })
						},
						{
							label: "只采集",
							icon: "globe",
							run: () => void T({ stage: "collect" })
						}
					]
				})
			]
		})]
	}), /* @__PURE__ */ q("div", {
		class: "library-processing-outcome",
		"aria-live": "polite",
		ref: S,
		children: [
			s.status === "running" && s.stalled && /* @__PURE__ */ q("div", {
				class: "library-processing-stalled",
				dangerouslySetInnerHTML: { __html: d("这个项目处理时间较长，暂时没有新进展。可以继续等待，或在任务结束后重试未完成项。", {
					variant: "warning",
					label: "处理较慢",
					filled: !0
				}) }
			}),
			(u || s.status === "failed") && /* @__PURE__ */ q("div", {
				role: "alert",
				onClick: (e) => {
					e.target.closest("[data-note-action]") && D();
				},
				dangerouslySetInnerHTML: { __html: d(u || s.error || "处理未完成，请重试", {
					variant: "error",
					filled: !0,
					actionLabel: A ? "重试未完成项" : "",
					details: j
				}) }
			}),
			g && /* @__PURE__ */ q("div", {
				class: "library-processing-result",
				dangerouslySetInnerHTML: { __html: d(`已扫描 ${s.scanned || 0} 个文件，识别 ${s.identified || 0} 个番号，整理 ${s.candidates || 0} 组资料候选。`, {
					variant: "success",
					label: "处理完成"
				}) }
			}),
			s.status !== "running" && !!k && /* @__PURE__ */ q("div", { dangerouslySetInnerHTML: { __html: d(k + (s.issues_log ? ` 完整记录：${s.issues_log}` : ""), { variant: "secondary" }) } })
		]
	})] });
}
//#endregion
//#region src/management.ts
function xt(e) {
	return e.filter((e) => ["115", "pikpak"].includes(e.location) && (e.roots === void 0 || e.roots.length > 0)).map((e) => e.location);
}
function St(e, t) {
	return t.filter((t) => e.some((e) => e.location === t));
}
function Ct() {
	let e = [
		["人工复核", "square-check-big"],
		["高清版", "sparkles"],
		["重复文件", "file-stack"],
		["垃圾文件", "file-archive"],
		["回收站", "trash"]
	], t = "<span class=\"skeleton cleanup-count-skeleton\" aria-hidden=\"true\"></span>";
	return `<div class="cleanuppage" data-skeleton="cleanup" aria-busy="true" aria-label="正在读取数据管理状态">
    <div class="cleanupstats">${e.map(([e, n]) => `
      <button type="button" class="board-plain-stat" disabled>
        <span class="board-plain-stat-head"><span class="board-stat-tile"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-${n}"></use></svg></span>${e}</span>
        <strong>${t}</strong><span class="cleanupmeta">${t}</span></button>`).join("")}</div>
    <div class="cleanupgrid">
      <section class="cleanupfieldset board-processing-skeleton" data-geist-fieldset aria-labelledby="cleanup-loading-scan">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-scan">扫描与采集</h3>
          <p>扫描媒体文件夹，导入已有资料，采集缺失信息。</p></div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><a class="board-link-button" href="/scraping"><span>来源和凭证</span><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-arrow-up"></use></svg></a><div class="splitbutton board-button-group primary"><button type="button" class="splitmain geist-button primary" disabled><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-database"></use></svg>扫描并补全资料</button><button type="button" class="splittoggle geist-button primary" disabled aria-label="更多扫描与采集方式"><svg aria-hidden="true"><use href="#i-chevron-down"></use></svg></button></div></footer>
      </section>
      <section class="cleanupfieldset cleanupemptyfolders" data-geist-fieldset aria-labelledby="cleanup-loading-empty">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-empty">空文件夹</h3>
          <strong>${t}</strong><p class="cleanupmeta">${t}</p></div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button type="button" disabled><svg aria-hidden="true"><use href="#i-scan-search"></use></svg><span>扫描空文件夹</span></button></footer>
      </section></div>
    <section class="resourcesync" aria-labelledby="cleanup-loading-links">
      <h2 id="cleanup-loading-links">链接管理</h2>
      <div class="resourcesyncbox" data-geist-fieldset>
        <div class="resourcesyncbody geist-fieldset-content"><h3 class="geist-fieldset-title">站外链接</h3>
          <div class="linksummary"><div class="linkstats">${[
		"链接总数",
		"官网/事务所",
		"社交账号",
		"作品资料站",
		"资料出处"
	].map((e) => `<div><span>${e}</span><b>${t}</b></div>`).join("")}</div></div></div>
        <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer><button class="resourceaction primary" type="button" disabled>检查死链</button></div>
      </div></section>
    <section class="resourcesync" aria-labelledby="cleanup-loading-sync">
      <h2 id="cleanup-loading-sync">资源同步</h2>
      <div class="resourcesyncbox" data-geist-fieldset>
        <div class="resourcesyncbody geist-fieldset-content"><h3 class="geist-fieldset-title">文件与记录核对</h3>
          <p>${t}</p></div>
        <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer><button class="resourceaction primary" type="button" disabled>检查文件</button></div>
      </div></section></div>`;
}
function wt(e, t = !1, n = !1) {
	if (t || n) return "";
	let r = "<svg class=\"externalmark\" viewBox=\"0 0 24 24\" aria-hidden=\"true\"><use href=\"#i-external-link\"></use></svg>";
	return `<details class="taste-history-guide"${e ? " open" : ""}>
    <summary><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"></use></svg>浏览器历史记录导入指南</summary>
    <div class="taste-history-guide-content">
      <p>在运行 Peach 的电脑上使用浏览器：点击上方「读取 Peach 主机」。</p>
      <p>记录在其他设备上：导出文件后，点击上方「导入历史」。多台设备的文件分别导入。</p>
      <ul><li>Chrome：在 <a class="externallink" href="https://takeout.google.com/" target="_blank" rel="noreferrer">Google Takeout${r}</a> 选择 Chrome 历史记录，下载 ZIP 后直接导入。</li>
      <li>其他浏览器：使用 <a class="externallink" href="https://github.com/purarue/browserexport" target="_blank" rel="noreferrer">browserexport${r}</a> 导出历史记录，再导入导出文件。</li></ul>
      <p>需要刷新时再次读取或导入；数据源可在页面底部移除。</p>
      <button type="button" class="geist-button taste-guide-skip">跳过</button>
    </div></details>`;
}
var Tt = "peach-taste-guide-dismissed";
function Et(e, t) {
	_(e, ".taste-history-guide", "taste-guide-collapse");
	let n = e.querySelector(".taste-history-guide");
	n?.querySelector(".taste-guide-skip")?.addEventListener("click", () => {
		t.setItem(Tt, "1"), n.remove();
	});
}
//#endregion
//#region src/board-state-preview.tsx
var Dt = [
	["idle", "待开始"],
	["loading", "页面加载"],
	["preparing", "准备任务"],
	["running", "任务进行中"],
	["retrying", "等待重试"],
	["disconnected", "失去连接"],
	["reconnected", "恢复连接"],
	["failed", "任务失败"],
	["complete", "任务完成"],
	["expired", "状态已失效"],
	["paused", "来源已暂停"]
], J = ({ html: e }) => /* @__PURE__ */ q("div", { dangerouslySetInnerHTML: { __html: e } });
function Ot() {
	let [e, t] = V("running"), [n, r] = V(0), [i, a] = V(document.documentElement.dataset.theme === "dark"), [o, s] = V(38), c = {
		status: e === "failed" ? "failed" : [
			"running",
			"preparing",
			"disconnected",
			"retrying",
			"reconnected"
		].includes(e) ? "running" : "idle",
		stage: e === "preparing" ? "正在准备扫描" : e === "retrying" ? "等待来源响应 · 8 秒后重试" : "正在整理资料",
		checked: o,
		...e === "preparing" ? {} : { total: 100 },
		error: e === "failed" ? "来源暂时不可用，请重试未完成项" : "",
		issue_count: +(e === "failed"),
		issue_preview: e === "failed" ? [{
			asset_id: null,
			title: "本地磁盘",
			path: "R:\\Media",
			message: "来源连接超时"
		}] : [],
		issues_log: e === "failed" ? "peach-data\\state\\library-processing-preview.issues.jsonl" : "",
		retryable_asset_ids: e === "failed" ? [7] : []
	}, u = e === "disconnected" ? "连接中断，正在重新读取处理进度" : "";
	return /* @__PURE__ */ q("main", {
		class: "board-state-preview",
		children: [
			/* @__PURE__ */ q("header", { children: [/* @__PURE__ */ q("div", { children: [/* @__PURE__ */ q("h1", { children: "运行状态预览" }), /* @__PURE__ */ q("p", { children: "演示数据 · 不连接任务接口，不执行扫描或写入。" })] }), /* @__PURE__ */ q("button", {
				class: "geist-button",
				onClick: () => {
					document.documentElement.dataset.theme = i ? "light" : "dark", a(!i);
				},
				children: i ? "浅色" : "深色"
			})] }),
			/* @__PURE__ */ q("nav", {
				"aria-label": "演示状态",
				children: Dt.map(([i, a]) => /* @__PURE__ */ q("button", {
					class: "geist-button",
					"aria-pressed": e === i,
					onClick: () => {
						t(i), r(n + 1);
					},
					children: a
				}))
			}),
			/* @__PURE__ */ q("div", {
				class: "board-preview-tools",
				children: [/* @__PURE__ */ q("label", { children: [
					"任务进度 ",
					/* @__PURE__ */ q("input", {
						type: "range",
						min: "0",
						max: "100",
						value: o,
						onInput: (e) => s(Number(e.currentTarget.value))
					}),
					/* @__PURE__ */ q("output", { children: [o, "%"] })
				] }), /* @__PURE__ */ q("button", {
					class: "geist-button",
					onClick: () => r(n + 1),
					children: "重播状态"
				})]
			}),
			/* @__PURE__ */ q("section", {
				"aria-label": "页面横幅",
				children: [
					/* @__PURE__ */ q("h2", { children: "全局任务横幅" }),
					/* @__PURE__ */ q(bt, {
						data: c,
						error: u,
						mode: "notice",
						preview: !0,
						toast: () => {}
					}, `banner-${e}-${n}-${o}`),
					![
						"running",
						"preparing",
						"disconnected",
						"retrying",
						"reconnected",
						"failed"
					].includes(e) && /* @__PURE__ */ q("p", { children: "此状态不常驻全局横幅。" })
				]
			}),
			/* @__PURE__ */ q("section", { children: [
				/* @__PURE__ */ q("h2", { children: "数据管理 · 扫描与采集" }),
				e === "loading" ? /* @__PURE__ */ q(J, { html: Ct() }) : /* @__PURE__ */ q("div", {
					class: "cleanupgrid",
					children: /* @__PURE__ */ q("div", {
						id: "libraryProcessing",
						class: "cleanupscraping",
						children: /* @__PURE__ */ q(bt, {
							data: c,
							error: u,
							preview: !0,
							toast: () => {}
						}, `${e}-${n}-${o}`)
					})
				}),
				e === "complete" && /* @__PURE__ */ q(J, { html: d("已完成扫描与资料采集", {
					variant: "success",
					label: "任务完成"
				}) }),
				e === "expired" && /* @__PURE__ */ q(J, { html: d("任务状态已失效，请重新发起任务", { variant: "warning" }) }),
				e === "paused" && /* @__PURE__ */ q("span", {
					class: "sbadge paused",
					children: "已暂停"
				})
			] }),
			/* @__PURE__ */ q("section", { children: [/* @__PURE__ */ q("h2", { children: "关注检查与资源同步" }), /* @__PURE__ */ q("div", {
				class: "board-preview-grid",
				children: [/* @__PURE__ */ q("article", { children: [/* @__PURE__ */ q("h3", { children: "检查更新" }), /* @__PURE__ */ q(J, { html: e === "disconnected" ? d("暂时无法读取进度，正在重新连接…", { label: "任务状态" }) : e === "failed" ? d("检查失败：来源连接超时", {
					variant: "error",
					actionLabel: "重试"
				}) : e === "running" || e === "retrying" || e === "reconnected" ? Ne(`${e === "retrying" ? "第 2/3 次尝试，8 秒后重试 · " : ""}已完成 ${o}/100 个来源`, o, 100) : e === "preparing" ? l("正在准备检查任务…") : d(e === "complete" ? "已完成检查" : e === "paused" ? "已暂停自动检查" : e === "expired" ? "任务状态已失效，请重新发起任务" : "等待开始", { variant: e === "complete" ? "success" : "secondary" }) })] }), /* @__PURE__ */ q("article", { children: [
					/* @__PURE__ */ q("h3", { children: "连接与恢复" }),
					/* @__PURE__ */ q(J, { html: f(e === "disconnected" ? "暂时无法连接服务器，正在重连" : e === "reconnected" ? "连接已恢复，继续读取任务进度" : "连接正常", {
						variant: e === "disconnected" ? "warning" : "gray",
						href: "#",
						label: "查看状态"
					}) }),
					/* @__PURE__ */ q("p", { children: "失去连接只影响进度读取；恢复连接后继续展示任务状态。" })
				] })]
			})] }),
			/* @__PURE__ */ q("section", { children: [/* @__PURE__ */ q("h2", { children: "错误与加载状态一览" }), /* @__PURE__ */ q("div", {
				class: "board-preview-grid",
				children: [
					/* @__PURE__ */ q("article", { children: [/* @__PURE__ */ q("h3", { children: "读取失败" }), /* @__PURE__ */ q(J, { html: d("无法读取状态，请重试", {
						variant: "error",
						actionLabel: "重试"
					}) })] }),
					/* @__PURE__ */ q("article", { children: [/* @__PURE__ */ q("h3", { children: "来源离线" }), /* @__PURE__ */ q(J, { html: d("媒体来源离线，请检查挂载状态", { variant: "warning" }) })] }),
					/* @__PURE__ */ q("article", { children: [/* @__PURE__ */ q("h3", { children: "没有待处理内容" }), /* @__PURE__ */ q(J, { html: d("没有待处理内容", { variant: "secondary" }) })] }),
					/* @__PURE__ */ q("article", { children: [/* @__PURE__ */ q("h3", { children: "等待响应" }), /* @__PURE__ */ q(J, { html: l("正在读取来源状态") })] })
				]
			})] })
		]
	});
}
function kt(e) {
	Ee(ie(Ot, {}), e);
}
//#endregion
//#region src/board-controls.ts
function At(e) {
	let t = Number(e.min) || 0, n = Number(e.max) || 100, r = Number(e.value), i = n > t ? Math.max(0, Math.min(100, (r - t) / (n - t) * 100)) : 0;
	e.style.setProperty("--board-range-value", `${i}%`);
	let a = e.closest(".dual-range");
	if (!a) return;
	let o = e.id === "durMax" ? "max" : "min", s = a.querySelector(`[data-range-end="${o}"]`);
	s || (s = document.createElement("output"), s.className = "board-range-tip", s.dataset.rangeEnd = o, s.setAttribute("aria-hidden", "true"), a.append(s)), s.textContent = r >= n && o === "max" ? "不限" : `${r} 分钟`, s.style.left = `${i}%`, s.style.setProperty("--range-tip-shift", "0px");
	let c = a.getBoundingClientRect(), l = s.getBoundingClientRect(), u = l.right > c.right ? c.right - l.right : l.left < c.left ? c.left - l.left : 0;
	u && s.style.setProperty("--range-tip-shift", `${Math.round(u)}px`), a.querySelectorAll(".board-range-tip").forEach((e) => e.toggleAttribute("data-range-active", e === s));
}
function jt() {
	let e = (e) => {
		e.querySelectorAll("input[type=range]").forEach(At), Ft(e), Nt(e), It(e);
	};
	e(document), new MutationObserver((t) => {
		for (let n of t) for (let t of n.addedNodes) t instanceof Element && (t.matches("input[type=range]") && At(t), e(t));
	}).observe(document.body, {
		subtree: !0,
		childList: !0
	}), document.addEventListener("input", (e) => {
		e.target instanceof HTMLInputElement && e.target.type === "range" && At(e.target);
	});
	let t = document.createElement("div");
	t.className = "board-tooltip", t.id = "board-control-tooltip", t.role = "tooltip", t.hidden = !0, document.body.append(t);
	let n = null, r = "", i = null, a, o = () => {
		clearTimeout(a), t.hidden = !0, n && (n.hasAttribute("title") || (n.title = r), i === null ? n.removeAttribute("aria-describedby") : n.setAttribute("aria-describedby", i)), n = null;
	}, s = (e, s) => {
		let c = e instanceof Element ? e.closest("[title]") : null;
		!c || c === n || c.closest(".vjs-control") || !c.title.trim() || (o(), n = c, r = c.title, i = c.getAttribute("aria-describedby"), c.removeAttribute("title"), a = setTimeout(() => {
			if (n !== c || !c.isConnected) return;
			t.textContent = r, t.hidden = !1;
			let e = c.getBoundingClientRect(), a = t.getBoundingClientRect();
			t.style.left = `${Math.max(8, Math.min(innerWidth - a.width - 8, e.left + (e.width - a.width) / 2))}px`, t.style.top = `${e.top >= a.height + 16 ? e.top - a.height - 8 : Math.min(innerHeight - a.height - 8, e.bottom + 8)}px`, c.setAttribute("aria-describedby", [i, t.id].filter(Boolean).join(" "));
		}, s));
	};
	document.addEventListener("pointerover", (e) => s(e.target, 400)), document.addEventListener("pointerout", (e) => {
		n && !n.contains(e.relatedTarget) && o();
	}), document.addEventListener("focusin", (e) => s(e.target, 0)), document.addEventListener("focusout", o), document.addEventListener("keydown", (e) => {
		e.key === "Escape" && o();
	}), document.addEventListener("scroll", o, !0), window.addEventListener("resize", o);
}
var Mt = /* @__PURE__ */ new Map();
function Nt(e) {
	let t = ".managebar-menu,.board-local-nav:not(.settingscard>.board-local-nav)", n = [...e.querySelectorAll(t)];
	e instanceof HTMLElement && e.matches(t) && n.push(e), n.forEach((e) => {
		if (e.hasAttribute("data-board-tabs")) return;
		e.dataset.boardTabs = "true";
		let t = e.className + e.getAttribute("aria-label"), n = (t) => {
			e.style.setProperty("--tab-x", `${t.left}px`), e.style.setProperty("--tab-width", `${t.width}px`);
		}, r = () => {
			let r = e.querySelector("button[aria-selected=true],button[aria-pressed=true]");
			if (!r || !r.offsetWidth) return;
			let i = {
				left: r.offsetLeft,
				width: r.offsetWidth
			};
			n(i), Mt.set(t, i);
		}, i = Mt.get(t);
		i ? n(i) : r(), requestAnimationFrame(() => {
			e.classList.add("board-tabs-ready"), requestAnimationFrame(r);
		});
		let a = new MutationObserver(r);
		a.observe(e, {
			subtree: !0,
			attributes: !0,
			attributeFilter: ["aria-selected", "aria-pressed"]
		});
		let o = new ResizeObserver(() => {
			if (!e.isConnected) {
				o.disconnect(), a.disconnect();
				return;
			}
			r();
		});
		o.observe(e);
	});
}
var Pt = /* @__PURE__ */ new Map();
function Ft(e) {
	let t = ".iconswitch,.insightswitch,.insighttabs,.follow-workspace-switch", n = [...e.querySelectorAll(t)];
	e instanceof HTMLElement && e.matches(t) && n.push(e), n.forEach((e) => {
		if (e.hasAttribute("data-board-segments") || e.closest("[data-skeleton]")) return;
		e.dataset.boardSegments = "true";
		let t = document.createElement("span");
		t.className = "board-segment-thumb", t.setAttribute("aria-hidden", "true"), e.prepend(t);
		let n = e.className + (e.getAttribute("aria-label") ?? ""), r = Pt.get(n) ?? null, i = () => {
			let i = e.querySelector("label:has(input:checked),button[aria-selected=true]");
			if (!i || !i.offsetWidth) return;
			let a = {
				x: i.offsetLeft,
				y: i.offsetTop,
				w: i.offsetWidth,
				h: i.offsetHeight
			};
			u(t, r, a, "x"), r = a, Pt.set(n, a);
		};
		e.addEventListener("change", i);
		let a = new MutationObserver(i);
		a.observe(e, {
			subtree: !0,
			attributes: !0,
			attributeFilter: ["aria-selected"]
		});
		let o = new ResizeObserver(() => {
			if (!e.isConnected) {
				o.disconnect(), a.disconnect();
				return;
			}
			i();
		});
		o.observe(e), i(), requestAnimationFrame(() => e.classList.add("board-segments-ready"));
	});
}
function It(e) {
	let t = ".board-ranked-chart,.board-radar,.tasteranks,.board-heat-card,.board-sankey-card", n = [...e.querySelectorAll(t)];
	e instanceof HTMLElement && e.matches(t) && n.push(e), n.forEach((e) => {
		if (e.hasAttribute("data-board-chart")) return;
		e.dataset.boardChart = "true", e.addEventListener("animationend", () => {
			e.getAnimations?.({ subtree: !0 }).some((e) => e.playState === "running") || e.classList.add("board-chart-settled");
		});
		let t = () => e.classList.add("board-chart-visible");
		if (typeof IntersectionObserver > "u" || matchMedia("(prefers-reduced-motion: reduce)").matches) {
			t();
			return;
		}
		let n = new IntersectionObserver((e) => {
			e.some((e) => e.isIntersecting) && (n.disconnect(), t());
		}, { threshold: .15 });
		n.observe(e);
	});
}
function Lt(e) {
	e.querySelectorAll(".tasteranks,.insightranking").forEach((e, t) => {
		if (e.children.length <= 5 || e.parentElement?.hasAttribute("data-expandable-ranks")) return;
		let n = document.createElement("div");
		n.className = "board-expand-ranks", n.dataset.expandableRanks = "", e.before(n), n.append(e), e.id = e.id || `board-rank-list-${t}`, e.classList.add("board-rank-list");
		let r = document.createElement("button");
		r.type = "button", r.className = "board-rank-expand", r.setAttribute("aria-controls", e.id), r.setAttribute("aria-expanded", "false"), r.setAttribute("aria-label", "展开更多排名"), r.innerHTML = "<svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><use href=\"#i-chevron-down\"/></svg>", n.append(r);
		let i = () => {
			let t = e.children[4];
			e.offsetWidth && (n.style.setProperty("--rank-collapsed-height", `${t.offsetTop - e.offsetTop + t.offsetHeight}px`), n.style.setProperty("--rank-expanded-height", `${e.scrollHeight}px`));
		}, a = () => {
			let t = r.getAttribute("aria-expanded") === "true";
			n.classList.toggle("expanded", t), [...e.children].forEach((e, n) => e.inert = !t && n >= 5), i();
		}, o = (t) => {
			t.target === e && n.classList.remove("toggling");
		};
		e.addEventListener("transitionend", o), e.addEventListener("transitioncancel", o);
		let s = () => {
			let e = r.getBoundingClientRect().top, t = performance.now() + 300, n = () => {
				let i = r.getBoundingClientRect().top - e;
				i && window.scrollBy(0, i), performance.now() < t && requestAnimationFrame(n);
			};
			n();
		};
		r.onclick = () => {
			let e = r.getAttribute("aria-expanded") !== "true";
			r.setAttribute("aria-expanded", String(e)), r.setAttribute("aria-label", e ? "收起排名" : "展开更多排名"), n.classList.add("toggling"), a(), e || s();
		}, new ResizeObserver(i).observe(e), a();
	});
}
//#endregion
//#region node_modules/d3-array/src/max.js
function Rt(e, t) {
	let n;
	if (t === void 0) for (let t of e) t != null && (n < t || n === void 0 && t >= t) && (n = t);
	else {
		let r = -1;
		for (let i of e) (i = t(i, ++r, e)) != null && (n < i || n === void 0 && i >= i) && (n = i);
	}
	return n;
}
//#endregion
//#region node_modules/d3-array/src/min.js
function zt(e, t) {
	let n;
	if (t === void 0) for (let t of e) t != null && (n > t || n === void 0 && t >= t) && (n = t);
	else {
		let r = -1;
		for (let i of e) (i = t(i, ++r, e)) != null && (n > i || n === void 0 && i >= i) && (n = i);
	}
	return n;
}
//#endregion
//#region node_modules/d3-array/src/sum.js
function Bt(e, t) {
	let n = 0;
	if (t === void 0) for (let t of e) (t = +t) && (n += t);
	else {
		let r = -1;
		for (let i of e) (i = +t(i, ++r, e)) && (n += i);
	}
	return n;
}
//#endregion
//#region node_modules/d3-sankey/src/align.js
function Vt(e, t) {
	return e.sourceLinks.length ? e.depth : t - 1;
}
//#endregion
//#region node_modules/d3-sankey/src/constant.js
function Ht(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-sankey/src/sankey.js
function Ut(e, t) {
	return Gt(e.source, t.source) || e.index - t.index;
}
function Wt(e, t) {
	return Gt(e.target, t.target) || e.index - t.index;
}
function Gt(e, t) {
	return e.y0 - t.y0;
}
function Kt(e) {
	return e.value;
}
function qt(e) {
	return e.index;
}
function Jt(e) {
	return e.nodes;
}
function Yt(e) {
	return e.links;
}
function Xt(e, t) {
	let n = e.get(t);
	if (!n) throw Error("missing: " + t);
	return n;
}
function Zt({ nodes: e }) {
	for (let t of e) {
		let e = t.y0, n = e;
		for (let n of t.sourceLinks) n.y0 = e + n.width / 2, e += n.width;
		for (let e of t.targetLinks) e.y1 = n + e.width / 2, n += e.width;
	}
}
function Qt() {
	let e = 0, t = 0, n = 1, r = 1, i = 24, a = 8, o, s = qt, c = Vt, l, u, d = Jt, f = Yt, p = 6;
	function m() {
		let e = {
			nodes: d.apply(null, arguments),
			links: f.apply(null, arguments)
		};
		return h(e), g(e), _(e), v(e), x(e), Zt(e), e;
	}
	m.update = function(e) {
		return Zt(e), e;
	}, m.nodeId = function(e) {
		return arguments.length ? (s = typeof e == "function" ? e : Ht(e), m) : s;
	}, m.nodeAlign = function(e) {
		return arguments.length ? (c = typeof e == "function" ? e : Ht(e), m) : c;
	}, m.nodeSort = function(e) {
		return arguments.length ? (l = e, m) : l;
	}, m.nodeWidth = function(e) {
		return arguments.length ? (i = +e, m) : i;
	}, m.nodePadding = function(e) {
		return arguments.length ? (a = o = +e, m) : a;
	}, m.nodes = function(e) {
		return arguments.length ? (d = typeof e == "function" ? e : Ht(e), m) : d;
	}, m.links = function(e) {
		return arguments.length ? (f = typeof e == "function" ? e : Ht(e), m) : f;
	}, m.linkSort = function(e) {
		return arguments.length ? (u = e, m) : u;
	}, m.size = function(i) {
		return arguments.length ? (e = t = 0, n = +i[0], r = +i[1], m) : [n - e, r - t];
	}, m.extent = function(i) {
		return arguments.length ? (e = +i[0][0], n = +i[1][0], t = +i[0][1], r = +i[1][1], m) : [[e, t], [n, r]];
	}, m.iterations = function(e) {
		return arguments.length ? (p = +e, m) : p;
	};
	function h({ nodes: e, links: t }) {
		for (let [t, n] of e.entries()) n.index = t, n.sourceLinks = [], n.targetLinks = [];
		let n = new Map(e.map((t, n) => [s(t, n, e), t]));
		for (let [e, r] of t.entries()) {
			r.index = e;
			let { source: t, target: i } = r;
			typeof t != "object" && (t = r.source = Xt(n, t)), typeof i != "object" && (i = r.target = Xt(n, i)), t.sourceLinks.push(r), i.targetLinks.push(r);
		}
		if (u != null) for (let { sourceLinks: t, targetLinks: n } of e) t.sort(u), n.sort(u);
	}
	function g({ nodes: e }) {
		for (let t of e) t.value = t.fixedValue === void 0 ? Math.max(Bt(t.sourceLinks, Kt), Bt(t.targetLinks, Kt)) : t.fixedValue;
	}
	function _({ nodes: e }) {
		let t = e.length, n = new Set(e), r = /* @__PURE__ */ new Set(), i = 0;
		for (; n.size;) {
			for (let e of n) {
				e.depth = i;
				for (let { target: t } of e.sourceLinks) r.add(t);
			}
			if (++i > t) throw Error("circular link");
			n = r, r = /* @__PURE__ */ new Set();
		}
	}
	function v({ nodes: e }) {
		let t = e.length, n = new Set(e), r = /* @__PURE__ */ new Set(), i = 0;
		for (; n.size;) {
			for (let e of n) {
				e.height = i;
				for (let { source: t } of e.targetLinks) r.add(t);
			}
			if (++i > t) throw Error("circular link");
			n = r, r = /* @__PURE__ */ new Set();
		}
	}
	function y({ nodes: t }) {
		let r = Rt(t, (e) => e.depth) + 1, a = (n - e - i) / (r - 1), o = Array(r);
		for (let n of t) {
			let t = Math.max(0, Math.min(r - 1, Math.floor(c.call(null, n, r))));
			n.layer = t, n.x0 = e + t * a, n.x1 = n.x0 + i, o[t] ? o[t].push(n) : o[t] = [n];
		}
		if (l) for (let e of o) e.sort(l);
		return o;
	}
	function b(e) {
		let n = zt(e, (e) => (r - t - (e.length - 1) * o) / Bt(e, Kt));
		for (let i of e) {
			let e = t;
			for (let t of i) {
				t.y0 = e, t.y1 = e + t.value * n, e = t.y1 + o;
				for (let e of t.sourceLinks) e.width = e.value * n;
			}
			e = (r - e + o) / (i.length + 1);
			for (let t = 0; t < i.length; ++t) {
				let n = i[t];
				n.y0 += e * (t + 1), n.y1 += e * (t + 1);
			}
			O(i);
		}
	}
	function x(e) {
		let n = y(e);
		o = Math.min(a, (r - t) / (Rt(n, (e) => e.length) - 1)), b(n);
		for (let e = 0; e < p; ++e) {
			let t = .99 ** e, r = Math.max(1 - t, (e + 1) / p);
			C(n, t, r), S(n, t, r);
		}
	}
	function S(e, t, n) {
		for (let r = 1, i = e.length; r < i; ++r) {
			let i = e[r];
			for (let e of i) {
				let n = 0, r = 0;
				for (let { source: t, value: i } of e.targetLinks) {
					let a = i * (e.layer - t.layer);
					n += k(t, e) * a, r += a;
				}
				if (!(r > 0)) continue;
				let i = (n / r - e.y0) * t;
				e.y0 += i, e.y1 += i, D(e);
			}
			l === void 0 && i.sort(Gt), w(i, n);
		}
	}
	function C(e, t, n) {
		for (let r = e.length - 2; r >= 0; --r) {
			let i = e[r];
			for (let e of i) {
				let n = 0, r = 0;
				for (let { target: t, value: i } of e.sourceLinks) {
					let a = i * (t.layer - e.layer);
					n += A(e, t) * a, r += a;
				}
				if (!(r > 0)) continue;
				let i = (n / r - e.y0) * t;
				e.y0 += i, e.y1 += i, D(e);
			}
			l === void 0 && i.sort(Gt), w(i, n);
		}
	}
	function w(e, n) {
		let i = e.length >> 1, a = e[i];
		E(e, a.y0 - o, i - 1, n), T(e, a.y1 + o, i + 1, n), E(e, r, e.length - 1, n), T(e, t, 0, n);
	}
	function T(e, t, n, r) {
		for (; n < e.length; ++n) {
			let i = e[n], a = (t - i.y0) * r;
			a > 1e-6 && (i.y0 += a, i.y1 += a), t = i.y1 + o;
		}
	}
	function E(e, t, n, r) {
		for (; n >= 0; --n) {
			let i = e[n], a = (i.y1 - t) * r;
			a > 1e-6 && (i.y0 -= a, i.y1 -= a), t = i.y0 - o;
		}
	}
	function D({ sourceLinks: e, targetLinks: t }) {
		if (u === void 0) {
			for (let { source: { sourceLinks: e } } of t) e.sort(Wt);
			for (let { target: { targetLinks: t } } of e) t.sort(Ut);
		}
	}
	function O(e) {
		if (u === void 0) for (let { sourceLinks: t, targetLinks: n } of e) t.sort(Wt), n.sort(Ut);
	}
	function k(e, t) {
		let n = e.y0 - (e.sourceLinks.length - 1) * o / 2;
		for (let { target: r, width: i } of e.sourceLinks) {
			if (r === t) break;
			n += i + o;
		}
		for (let { source: r, width: i } of t.targetLinks) {
			if (r === e) break;
			n -= i;
		}
		return n;
	}
	function A(e, t) {
		let n = t.y0 - (t.targetLinks.length - 1) * o / 2;
		for (let { source: r, width: i } of t.targetLinks) {
			if (r === e) break;
			n += i + o;
		}
		for (let { target: r, width: i } of e.sourceLinks) {
			if (r === t) break;
			n -= i;
		}
		return n;
	}
	return m;
}
//#endregion
//#region node_modules/d3-path/src/path.js
var $t = Math.PI, en = 2 * $t, Y = 1e-6, tn = en - Y;
function nn() {
	this._x0 = this._y0 = this._x1 = this._y1 = null, this._ = "";
}
function rn() {
	return new nn();
}
nn.prototype = rn.prototype = {
	constructor: nn,
	moveTo: function(e, t) {
		this._ += "M" + (this._x0 = this._x1 = +e) + "," + (this._y0 = this._y1 = +t);
	},
	closePath: function() {
		this._x1 !== null && (this._x1 = this._x0, this._y1 = this._y0, this._ += "Z");
	},
	lineTo: function(e, t) {
		this._ += "L" + (this._x1 = +e) + "," + (this._y1 = +t);
	},
	quadraticCurveTo: function(e, t, n, r) {
		this._ += "Q" + +e + "," + +t + "," + (this._x1 = +n) + "," + (this._y1 = +r);
	},
	bezierCurveTo: function(e, t, n, r, i, a) {
		this._ += "C" + +e + "," + +t + "," + +n + "," + +r + "," + (this._x1 = +i) + "," + (this._y1 = +a);
	},
	arcTo: function(e, t, n, r, i) {
		e = +e, t = +t, n = +n, r = +r, i = +i;
		var a = this._x1, o = this._y1, s = n - e, c = r - t, l = a - e, u = o - t, d = l * l + u * u;
		if (i < 0) throw Error("negative radius: " + i);
		if (this._x1 === null) this._ += "M" + (this._x1 = e) + "," + (this._y1 = t);
		else if (d > Y) {
			if (!(Math.abs(u * s - c * l) > Y) || !i) this._ += "L" + (this._x1 = e) + "," + (this._y1 = t);
			else {
				var f = n - a, p = r - o, m = s * s + c * c, h = f * f + p * p, g = Math.sqrt(m), _ = Math.sqrt(d), v = i * Math.tan(($t - Math.acos((m + d - h) / (2 * g * _))) / 2), y = v / _, b = v / g;
				Math.abs(y - 1) > Y && (this._ += "L" + (e + y * l) + "," + (t + y * u)), this._ += "A" + i + "," + i + ",0,0," + +(u * f > l * p) + "," + (this._x1 = e + b * s) + "," + (this._y1 = t + b * c);
			}
		}
	},
	arc: function(e, t, n, r, i, a) {
		e = +e, t = +t, n = +n, a = !!a;
		var o = n * Math.cos(r), s = n * Math.sin(r), c = e + o, l = t + s, u = 1 ^ a, d = a ? r - i : i - r;
		if (n < 0) throw Error("negative radius: " + n);
		this._x1 === null ? this._ += "M" + c + "," + l : (Math.abs(this._x1 - c) > Y || Math.abs(this._y1 - l) > Y) && (this._ += "L" + c + "," + l), n && (d < 0 && (d = d % en + en), d > tn ? this._ += "A" + n + "," + n + ",0,1," + u + "," + (e - o) + "," + (t - s) + "A" + n + "," + n + ",0,1," + u + "," + (this._x1 = c) + "," + (this._y1 = l) : d > Y && (this._ += "A" + n + "," + n + ",0," + +(d >= $t) + "," + u + "," + (this._x1 = e + n * Math.cos(i)) + "," + (this._y1 = t + n * Math.sin(i))));
	},
	rect: function(e, t, n, r) {
		this._ += "M" + (this._x0 = this._x1 = +e) + "," + (this._y0 = this._y1 = +t) + "h" + +n + "v" + +r + "h" + -n + "Z";
	},
	toString: function() {
		return this._;
	}
};
//#endregion
//#region node_modules/d3-shape/src/constant.js
function an(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-shape/src/point.js
function on(e) {
	return e[0];
}
function sn(e) {
	return e[1];
}
//#endregion
//#region node_modules/d3-shape/src/array.js
var cn = Array.prototype.slice;
//#endregion
//#region node_modules/d3-shape/src/link/index.js
function ln(e) {
	return e.source;
}
function un(e) {
	return e.target;
}
function dn(e) {
	var t = ln, n = un, r = on, i = sn, a = null;
	function o() {
		var o, s = cn.call(arguments), c = t.apply(this, s), l = n.apply(this, s);
		if (a ||= o = rn(), e(a, +r.apply(this, (s[0] = c, s)), +i.apply(this, s), +r.apply(this, (s[0] = l, s)), +i.apply(this, s)), o) return a = null, o + "" || null;
	}
	return o.source = function(e) {
		return arguments.length ? (t = e, o) : t;
	}, o.target = function(e) {
		return arguments.length ? (n = e, o) : n;
	}, o.x = function(e) {
		return arguments.length ? (r = typeof e == "function" ? e : an(+e), o) : r;
	}, o.y = function(e) {
		return arguments.length ? (i = typeof e == "function" ? e : an(+e), o) : i;
	}, o.context = function(e) {
		return arguments.length ? (a = e ?? null, o) : a;
	}, o;
}
function fn(e, t, n, r, i) {
	e.moveTo(t, n), e.bezierCurveTo(t = (t + r) / 2, n, t, i, r, i);
}
function pn() {
	return dn(fn);
}
//#endregion
//#region node_modules/d3-sankey/src/sankeyLinkHorizontal.js
function mn(e) {
	return [e.source.x1, e.y0];
}
function hn(e) {
	return [e.target.x0, e.y1];
}
function gn() {
	return pn().source(mn).target(hn);
}
//#endregion
//#region src/board-sankey.ts
function _n(t = []) {
	let n = t.filter((e) => e.source && e.target && Number.isFinite(e.value) && e.value > 0);
	if (!n.length) return "";
	let r = [...new Set(n.map((e) => e.source))], i = [...new Set(n.map((e) => e.target))], a = Qt().nodeId((e) => e.id).nodeWidth(10).nodePadding(22).extent([[155, 16], [535, 404]])({
		nodes: [...r.map((e) => ({
			id: `source:${e}`,
			name: e,
			side: "source"
		})), ...i.map((e) => ({
			id: `target:${e}`,
			name: e,
			side: "target"
		}))],
		links: n.map((e) => ({
			source: `source:${e.source}`,
			target: `target:${e.target}`,
			value: e.value
		}))
	}), o = n.reduce((e, t) => e + t.value, 0), s = gn(), c = a.links.map((t) => {
		let n = t.source, i = t.target;
		return `<path d="${s(t)}" stroke-width="${Math.max(.5, t.width || 0)}" style="--flow-color:var(--board-chart-${r.indexOf(n.name) % 6})" data-flow-source="${n.index}" data-flow-target="${i.index}" data-flow-value="${t.value}" data-flow-label="${e(n.name)} → ${e(i.name)}" tabindex="0" role="img" aria-label="${e(n.name)} → ${e(i.name)}：${t.value} 条线索"/>`;
	}).join(""), l = a.nodes.map((t) => `<g data-flow-node="${t.index}" data-flow-value="${t.value}" data-flow-label="${e(t.name)}" tabindex="0" role="img" aria-label="${e(t.name)}：${t.value} 条线索"><rect x="${t.x0}" y="${t.y0}" width="10" height="${Math.max(1, (t.y1 || 0) - (t.y0 || 0))}" rx="5" fill="${t.side === "source" ? `var(--board-chart-${r.indexOf(t.name) % 6})` : "var(--color-text-secondary)"}"/><text x="${t.side === "source" ? 145 : 545}" y="${((t.y0 || 0) + (t.y1 || 0)) / 2}" text-anchor="${t.side === "source" ? "end" : "start"}" dominant-baseline="middle">${e(t.name.length > 18 ? t.name.slice(0, 16) + "…" : t.name)}<tspan x="${t.side === "source" ? 145 : 545}" dy="15">${t.side === "source" ? t.value?.toLocaleString() : ((t.value || 0) / o * 100).toFixed(1) + "%"}</tspan></text></g>`).join("");
	return `<section class="board-sankey-card" data-sankey-card><header><h3>创作者线索来源</h3><b data-sankey-number>${o.toLocaleString()}</b><span data-sankey-label>条线索</span></header><div class="board-sankey-scroll"><svg viewBox="0 0 720 435" aria-label="来源网站与创作者线索"><g class="board-sankey-links">${c}</g><g class="board-sankey-nodes">${l}</g></svg></div><footer><span>来源网站</span><span>创作者 · 线索占比</span></footer></section>`;
}
function vn(e) {
	e.querySelectorAll("[data-sankey-card]").forEach((e) => {
		let t = [...e.querySelectorAll("[data-flow-source]")], n = [...e.querySelectorAll("[data-flow-node]")], r = e.querySelector("[data-sankey-number]"), i = e.querySelector("[data-sankey-label]"), a = r.textContent, o = () => {
			t.forEach((e) => e.style.opacity = ""), n.forEach((e) => e.style.opacity = ""), r.textContent = a, i.textContent = "条线索";
		};
		[...t, ...n].forEach((e) => {
			let a = () => {
				let a = e.dataset.flowNode;
				t.forEach((t) => t.style.opacity = String((a === void 0 ? t === e : t.dataset.flowSource === a || t.dataset.flowTarget === a) ? .7 : .08)), n.forEach((n) => n.style.opacity = String(a === void 0 ? n.dataset.flowNode === e.dataset.flowSource || n.dataset.flowNode === e.dataset.flowTarget ? 1 : .3 : n === e || t.some((e) => e.dataset.flowSource === a && e.dataset.flowTarget === n.dataset.flowNode || e.dataset.flowTarget === a && e.dataset.flowSource === n.dataset.flowNode) ? 1 : .3)), r.textContent = Number(e.dataset.flowValue).toLocaleString(), i.textContent = e.dataset.flowLabel;
			};
			e.addEventListener("pointerenter", a), e.addEventListener("pointerleave", o), e.addEventListener("focus", a), e.addEventListener("blur", o);
		});
	});
}
//#endregion
//#region src/board-analytics.ts
var yn = (e) => Number.isFinite(e) && e >= 0;
function bn(t, n, r = "个视频") {
	let i = t.filter((e) => yn(e.value));
	if (!i.length) return "";
	let a = i.reduce((e, t) => e + t.value, 0), o = Math.max(1, ...i.map((e) => e.value)) * 1.1, s = Math.min(22, 110 / Math.max(1, i.length)), c = Math.min(15, s * .68), l = i.map((t, n) => {
		let i = 32 + n * s, a = t.value / o * 100;
		return `<g style="--ring-color:var(--board-chart-${n % 6});--ring-delay:${n * 60}ms"><circle class="board-ring-track" cx="160" cy="160" r="${i}" stroke-width="${c}"/><circle class="board-ring-value" data-radial-ring="${n}" tabindex="0" role="button" aria-label="${e(t.name)}：${t.value.toLocaleString()} ${e(r)}" aria-pressed="false" cx="160" cy="160" r="${i}" stroke-width="${c}" pathLength="100" stroke-dasharray="${a} ${100 - a}" style="--ring-length:${a}" transform="rotate(-90 160 160)"/></g>`;
	}).join("");
	return `<section class="board-radial-card" data-radial-card data-radial-total="${a}" data-radial-title="${e(n)}"><header><span data-radial-label>${e(n)}</span><b data-radial-number>${a.toLocaleString()}</b><small>${e(r)}</small></header><svg class="board-rings" viewBox="0 0 320 320" aria-label="${e(n)}">${l}</svg><div class="board-radial-tiles">${i.map((t, n) => `<button type="button" data-radial-tile="${n}" data-radial-value="${t.value}" data-radial-name="${e(t.name)}" aria-pressed="false" style="--ring-color:var(--board-chart-${n % 6})"><span><i aria-hidden="true"></i>${e(t.name)}</span><b>${t.value.toLocaleString()}</b>${t.detail ? `<small>${e(t.detail)}</small>` : ""}</button>`).join("")}</div></section>`;
}
function xn(e) {
	e.querySelectorAll("[data-radial-card]").forEach((e) => {
		let t = [...e.querySelectorAll("[data-radial-tile]")], n = [...e.querySelectorAll("[data-radial-ring]")], r = e.querySelector("[data-radial-number]"), i = e.querySelector("[data-radial-label]"), a = -1, o = 0, s = 0, c = (c, l = 300) => {
			e.dataset.radialFocus = String(c), t.forEach((e, t) => {
				e.dataset.active = String(t === c), e.setAttribute("aria-pressed", String(t === a)), n[t]?.setAttribute("aria-pressed", String(t === a)), n[t] && (n[t].dataset.active = String(t === c));
			});
			let u = Number(c < 0 ? e.dataset.radialTotal : t[c]?.dataset.radialValue);
			i.textContent = c < 0 ? e.dataset.radialTitle : t[c].dataset.radialName, cancelAnimationFrame(s);
			let d = o, f = performance.now(), p = (t) => {
				if (!e.isConnected) return;
				let n = matchMedia("(prefers-reduced-motion: reduce)").matches ? 1 : Math.min(1, (t - f) / l);
				o = d + (u - d) * (1 - (1 - n) ** 3), r.textContent = Math.round(o).toLocaleString(), n < 1 && (s = requestAnimationFrame(p));
			};
			s = requestAnimationFrame(p);
		}, l = (e) => {
			a = a === e ? -1 : e, c(a);
		};
		[...t, ...n].forEach((e) => {
			let t = Number(e.getAttribute("data-radial-tile") ?? e.getAttribute("data-radial-ring"));
			e.addEventListener("pointerenter", () => c(t)), e.addEventListener("pointerleave", () => c(a)), e.addEventListener("focus", () => c(t)), e.addEventListener("blur", () => c(a)), e.addEventListener("click", () => l(t)), e instanceof SVGElement && e.addEventListener("keydown", (e) => {
				(e.key === "Enter" || e.key === " ") && (e.preventDefault(), l(t));
			});
		}), e.dataset.radialFocus = "-1", r.textContent = "0";
		let u = () => {
			requestAnimationFrame(() => {
				e.isConnected && (e.classList.add("board-chart-visible"), c(-1, 1200));
			});
		};
		if (typeof IntersectionObserver > "u" || matchMedia("(prefers-reduced-motion: reduce)").matches) u();
		else {
			let t = new IntersectionObserver((e) => {
				e.some((e) => e.isIntersecting) && (t.disconnect(), u());
			}, { threshold: .15 });
			t.observe(e);
		}
	});
}
var Sn = [
	"周一",
	"周二",
	"周三",
	"周四",
	"周五",
	"周六",
	"周日"
];
function Cn(t) {
	if (!t?.days?.length) return "<section class=\"board-activity-empty\"><h3>浏览活跃时间</h3><p>还没有可用于分析的口味网站访问记录。</p></section>";
	let n = Array.from({ length: 7 }, () => Array(24).fill(0));
	for (let e of t.hours || []) Number.isInteger(e.weekday) && e.weekday >= 0 && e.weekday < 7 && Number.isInteger(e.hour) && e.hour >= 0 && e.hour < 24 && yn(e.count) && (n[e.weekday][e.hour] = (n[e.weekday][e.hour] || 0) + e.count);
	let r = Math.max(1, ...n.flat()), i = n.flat().reduce((e, t) => e + t, 0), a = n.map((e, t) => `<span class="board-heat-axis">${Sn[t]}</span>${e.map((e, n) => `<button type="button" data-heat-value="${e}" data-heat-label="${Sn[t]} ${n}:00" aria-label="${Sn[t]} ${n}:00，${e} 次访问" style="--heat:${e ? Math.max(12, e / r * 100) : 0}%"></button>`).join("")}`).join(""), o = t.days.filter((e) => /^\d{4}-\d{2}-\d{2}$/.test(e.date) && yn(e.count)).sort((e, t) => e.date.localeCompare(t.date));
	if (!o.length) return "";
	let s = /* @__PURE__ */ new Date(`${o.at(-1).date}T00:00:00Z`), c = new Date(s);
	c.setUTCDate(c.getUTCDate() - 90);
	let l = new Map(o.map((e) => [e.date, e.count])), u = Math.max(1, ...o.map((e) => e.count)), d = Array.from({ length: 91 }, (e, t) => {
		let n = new Date(c);
		n.setUTCDate(c.getUTCDate() + t);
		let r = n.toISOString().slice(0, 10), i = l.get(r) || 0;
		return `<button type="button" data-heat-value="${i}" data-heat-label="${r}" aria-label="${r}，${i} 次访问" style="--heat:${i ? Math.max(12, i / u * 100) : 0}%"></button>`;
	}).join("");
	return `<div class="board-activity-charts"><section class="board-heat-card" data-heat-card><header><h3>浏览活跃时间</h3><b data-heat-number>${i.toLocaleString()}</b><span data-heat-title data-heat-default="口味网站访问">口味网站访问</span></header><div class="board-heat-scroll"><div class="board-hour-grid"><span></span>${Array.from({ length: 24 }, (e, t) => `<span class="board-heat-axis">${t % 2 ? "" : t}</span>`).join("")}${a}</div></div><footer>星期 × 小时<span>${e(t.timezone || "UTC+08:00")}</span></footer></section><section class="board-heat-card" data-heat-card><header><h3>每日活跃</h3><b data-heat-number>${o.filter((e) => e.date >= c.toISOString().slice(0, 10)).reduce((e, t) => e + t.count, 0).toLocaleString()}</b><span data-heat-title data-heat-default="口味网站访问">口味网站访问</span></header><div class="board-day-grid">${d}</div><footer>${c.toISOString().slice(0, 10)}<span>${o.at(-1).date}</span></footer></section></div>`;
}
function wn(e) {
	e.querySelectorAll("[data-heat-card]").forEach((e) => {
		let t = e.querySelector("[data-heat-number]"), n = e.querySelector("[data-heat-title]"), r = t.textContent;
		e.querySelectorAll("[data-heat-value]").forEach((e) => {
			let i = () => {
				t.textContent = Number(e.dataset.heatValue).toLocaleString(), n.textContent = e.dataset.heatLabel;
			}, a = () => {
				t.textContent = r, n.textContent = n.dataset.heatDefault;
			};
			e.addEventListener("pointerenter", i), e.addEventListener("pointerleave", a), e.addEventListener("focus", i), e.addEventListener("blur", a);
		});
	});
}
//#endregion
//#region src/sidebar-groups.ts
var Tn = (e) => e.replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]);
function En(e, t, n = "", r = "") {
	if (!t) return "";
	let i = `sidebar-group-${encodeURIComponent(e)}`;
	return `<details class="sec${r ? " cat-" + Tn(r) : ""}" data-sidebar-group="${Tn(e)}"><summary role="button" class="board-section-toggle"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"/></svg><span>${Tn(e)}</span></summary><div class="board-sidebar-body" id="${i}">${t}${n}</div></details>`;
}
function Dn(e) {
	e.querySelectorAll("[data-sidebar-group]").forEach((e) => {
		if (e.dataset.sidebarWired) return;
		e.dataset.sidebarWired = "true";
		let t = e.querySelector(".board-sidebar-body"), n = `peach.sidebar.group.${e.dataset.sidebarGroup}`, r = null;
		try {
			r = sessionStorage.getItem(n);
		} catch {}
		let i = !!t.querySelector("[aria-pressed=true]");
		e.open = r === null ? i : r === "open";
	}), _(e, "details[data-sidebar-group]", "sidebar-collapse"), e.querySelectorAll(".board-section-toggle").forEach((e) => {
		e.dataset.persistWired || (e.dataset.persistWired = "true", e.addEventListener("click", () => {
			let t = `peach.sidebar.group.${e.closest("[data-sidebar-group]").dataset.sidebarGroup}`;
			try {
				sessionStorage.setItem(t, e.getAttribute("aria-expanded") === "true" ? "open" : "closed");
			} catch {}
		}));
	});
}
var On = !1;
async function kn(e, t) {
	if (On) return;
	if (!document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) {
		t();
		return;
	}
	let n = e.getBoundingClientRect(), r = n.left + n.width / 2, i = n.top + n.height / 2, a = Math.hypot(Math.max(r, innerWidth - r), Math.max(i, innerHeight - i)) * 2.5, o = document.createElement("style");
	o.textContent = `::view-transition-old(root){animation:none}::view-transition-new(root){mix-blend-mode:normal;mask-image:radial-gradient(circle closest-side,#000 78%,#0006 88%,transparent);mask-repeat:no-repeat;will-change:mask-position,mask-size;animation:peach-theme-reveal 560ms cubic-bezier(.16,1,.3,1) both}@keyframes peach-theme-reveal{from{mask-position:${r}px ${i}px;mask-size:0px 0px}to{mask-position:${r - a / 2}px ${i - a / 2}px;mask-size:${a}px ${a}px}}`, On = !0, document.head.append(o);
	let s = document.documentElement;
	s.dataset.themeSnapshot = "true";
	let c = !1, l = () => {
		c || (c = !0, t());
	};
	try {
		await document.startViewTransition(l).finished;
	} catch {
		l();
	} finally {
		delete s.dataset.themeSnapshot, o.remove(), On = !1;
	}
}
//#endregion
//#region src/configuration-endpoints.ts
var An = "/api/configuration";
//#endregion
//#region src/react-slot.tsx
function jn({ mount: e, props: t }) {
	let n = U(null), r = U(null), i = U(t);
	i.current = t;
	let [a, o] = V("");
	return H(() => {
		let t = !1;
		return import("/dist/peach-react.js").then((a) => {
			if (t || !n.current) return;
			let o = a[e];
			r.current = o(n.current, i.current);
		}, (e) => {
			t || o(e instanceof Error ? e.message : String(e));
		}), () => {
			t = !0, r.current?.unmount(), r.current = null;
		};
	}, [e]), H(() => {
		r.current?.update(t);
	}), a ? /* @__PURE__ */ q("p", {
		class: "configbad",
		role: "alert",
		children: ["界面组件没有加载：", a]
	}) : /* @__PURE__ */ q("div", {
		ref: n,
		class: "peach-react"
	});
}
//#endregion
//#region src/islands/configuration.tsx
var Mn = (e, t) => G(An, t);
function Nn({ receipt: e, data: t, error: n }) {
	if (n || !t) return /* @__PURE__ */ q("div", {
		class: "configpage",
		dangerouslySetInnerHTML: { __html: d(n || "没有读到配置", {
			variant: "error",
			label: "打不开配置"
		}) }
	});
	let r = {
		data: t,
		receipt: e
	};
	return /* @__PURE__ */ q("div", {
		class: "configpage",
		children: [
			t.startup ? /* @__PURE__ */ q("h2", {
				class: "configgroup",
				children: "通用"
			}) : null,
			t.startup ? /* @__PURE__ */ q(jn, {
				mount: "mountGeneralSettings",
				props: r
			}) : null,
			/* @__PURE__ */ q("h2", {
				class: "configgroup",
				children: "媒体"
			}),
			/* @__PURE__ */ q(jn, {
				mount: "mountMediaSettings",
				props: r
			}),
			t.peach_proxy || t.access ? /* @__PURE__ */ q("h2", {
				class: "configgroup",
				children: "网络与访问"
			}) : null,
			t.peach_proxy || t.access ? /* @__PURE__ */ q(jn, {
				mount: "mountNetworkSettings",
				props: r
			}) : null,
			/* @__PURE__ */ q("h2", {
				class: "configgroup",
				children: "更新与维护"
			}),
			/* @__PURE__ */ q(jn, {
				mount: "mountMaintenanceSettings",
				props: r
			})
		]
	});
}
//#endregion
//#region src/islands/scraping.tsx
var Pn = (e, t) => G("/api/scraping", t);
function Fn({ value: e, onChange: t }) {
	let n = U(null), r = U(t);
	return r.current = t, Ye(() => {
		let t = n.current;
		t.innerHTML = p([["peach", "Peach 代理"], ["direct", "直接连接"]], e, { label: "连接方式" });
		let i = v(t.firstElementChild), a = () => r.current(i.value);
		return i.addEventListener("change", a), () => {
			i.disabled = !0, i.removeEventListener("change", a), t.replaceChildren();
		};
	}, []), /* @__PURE__ */ q("div", {
		ref: n,
		class: "scraping-network"
	});
}
function In({ source: e, toast: t }) {
	let [n, i] = V(e), [a, o] = V(e.network), [s, l] = V(""), [u, f] = V(""), [p, m] = V("paste"), [g, _] = V(""), [v, y] = V(!1), [b, x] = V(""), [S, C] = V([]), w = U(null), T = U(null);
	Ye(() => {
		T.current?.querySelectorAll("footer button").forEach((e) => h(e, v));
	}, [v]);
	let E = U(new AbortController());
	H(() => () => E.current.abort(), []);
	async function D(n) {
		if (!v) {
			y(!0), x(""), C([]);
			try {
				if (n === "check") {
					let t = await K("/api/scraping/check", { source: e.source }, "POST", E.current.signal);
					E.current.signal.aborted || C(t.results);
				} else {
					let r = await K("/api/scraping/settings", {
						source: e.source,
						network: a,
						cookie: s,
						cookies_text: u,
						revoke: n === "revoke"
					}, "POST", E.current.signal);
					E.current.signal.aborted || (i(r.saved), l(""), f(""), _(""), w.current && (w.current.value = ""), t(n === "revoke" ? "Cookie 已撤销" : "来源设置已保存"));
				}
			} catch (e) {
				E.current.signal.aborted || x(W(e));
			} finally {
				E.current.signal.aborted || y(!1);
			}
		}
	}
	return /* @__PURE__ */ q("section", {
		class: "scraping-source",
		children: /* @__PURE__ */ q("form", {
			ref: T,
			class: "cleanupfieldset",
			"data-geist-fieldset": !0,
			onSubmit: (e) => {
				e.preventDefault(), D("save");
			},
			children: [/* @__PURE__ */ q("div", {
				class: "geist-fieldset-content scraping-fields",
				children: [
					/* @__PURE__ */ q("div", {
						class: "geist-fieldset-heading",
						children: [/* @__PURE__ */ q("div", { dangerouslySetInnerHTML: { __html: c(`scraping-${e.source}`, e.label) } }), /* @__PURE__ */ q("a", {
							class: "scraping-url externallink",
							href: e.login,
							target: "_blank",
							rel: "noopener noreferrer",
							children: [
								/* @__PURE__ */ q("img", {
									src: r({ source: e.source }),
									alt: "",
									width: "16",
									height: "16",
									loading: "lazy",
									onError: (e) => e.currentTarget.remove()
								}),
								/* @__PURE__ */ q("span", { children: e.login }),
								/* @__PURE__ */ q("svg", {
									class: "externalmark",
									viewBox: "0 0 24 24",
									"aria-hidden": "true",
									children: /* @__PURE__ */ q("use", { href: "#i-external-link" })
								})
							]
						})]
					}),
					/* @__PURE__ */ q("div", {
						class: "scraping-label",
						children: ["连接方式", /* @__PURE__ */ q(Fn, {
							value: a,
							onChange: o
						})]
					}),
					a === "peach" && /* @__PURE__ */ q(ut, {
						href: "/configuration#peachProxy",
						children: "配置 Peach 代理"
					}),
					e.accepts_cookie && /* @__PURE__ */ q(F, { children: [
						/* @__PURE__ */ q("p", { children: n.cookie_saved ? "Cookie 已保存，登录是否有效请在抓取时确认。" : "需要登录时，任选一种方式提供 Cookie。" }),
						/* @__PURE__ */ q("div", {
							class: "insightswitch scraping-cookie-method",
							role: "radiogroup",
							"aria-label": "提供 Cookie 的方式（二选一）",
							children: [["paste", "粘贴 Cookie"], ["file", "导入文件"]].map(([t, n]) => /* @__PURE__ */ q("label", { children: [/* @__PURE__ */ q("input", {
								type: "radio",
								name: `cookie-method-${e.source}`,
								value: t,
								checked: p === t,
								onChange: () => {
									m(t), l(""), f(""), _("");
								}
							}), /* @__PURE__ */ q("span", { children: n })] }, t))
						}),
						p === "paste" ? /* @__PURE__ */ q("label", { children: ["Cookie", /* @__PURE__ */ q("input", {
							class: "geist-input",
							type: "password",
							autoComplete: "off",
							value: s,
							disabled: v,
							onInput: (e) => l(e.currentTarget.value)
						})] }) : /* @__PURE__ */ q("label", {
							class: "scraping-file",
							children: ["Netscape Cookie 文件（.txt）", /* @__PURE__ */ q("span", {
								class: "scraping-file-control",
								children: [
									/* @__PURE__ */ q("span", {
										class: "geist-button",
										children: "选择文件"
									}),
									/* @__PURE__ */ q("span", {
										class: "scraping-file-name",
										children: g || "未选择文件"
									}),
									/* @__PURE__ */ q("input", {
										ref: w,
										type: "file",
										accept: ".txt",
										disabled: v,
										onChange: async (e) => {
											let t = e.currentTarget.files?.[0];
											if (!t) {
												f(""), _("");
												return;
											}
											if (f(""), t.size > 262144) {
												x("Cookie 文本超过 256 KiB"), e.currentTarget.value = "";
												return;
											}
											y(!0);
											try {
												let e = await t.text();
												E.current.signal.aborted || (f(e), _(t.name));
											} catch {
												E.current.signal.aborted || x("Cookie 文件未读取，请重新选择");
											} finally {
												E.current.signal.aborted || y(!1);
											}
										}
									})
								]
							})]
						})
					] }),
					b && /* @__PURE__ */ q("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: d(b, { variant: "error" }) }
					}),
					S.map((t) => /* @__PURE__ */ q("div", {
						role: "status",
						dangerouslySetInnerHTML: { __html: d(`${e.label}${t.label === "来源页面" ? "" : " 高清图片"}：${t.ok ? "可连接" : "不能连接"}` + (t.width ? ` · ${t.width} × ${t.height}` : "") + (t.message ? `。${t.message}` : ""), { variant: t.ok ? "success" : "error" }) }
					}, t.label))
				]
			}), /* @__PURE__ */ q("footer", {
				class: "geist-fieldset-footer",
				"data-geist-fieldset-footer": !0,
				children: [
					e.accepts_cookie && n.cookie_saved && /* @__PURE__ */ q("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void D("revoke"),
						children: "撤销 Cookie"
					}),
					/* @__PURE__ */ q("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void D("check"),
						children: "检查连接"
					}),
					/* @__PURE__ */ q("button", {
						class: "geist-button primary",
						type: "submit",
						children: "保存"
					})
				]
			})]
		})
	});
}
function Ln({ data: e, error: t, toast: n }) {
	let [r, i] = V(""), [a, o] = V(!1), [s, u] = V(""), [f, p] = V(""), m = U(null);
	Ye(() => h(m.current, a), [a]);
	let g = U(new AbortController()), _ = U(0);
	async function v(e = !1) {
		let t = ++_.current;
		await st({
			read: (e) => G("/api/scraping/cover", e),
			active: () => !g.current.signal.aborted && t === _.current,
			render: (t) => {
				o(t.status === "running"), t.status === "running" && (e = !1), t.status === "failed" && !e && u(t.error || "采集未取得"), t.status === "complete" && !e && (p(t.result || "封面采集完成"), n(t.result || "封面采集完成"));
			},
			disconnected: () => u("连接中断，正在重新读取后台进度")
		});
	}
	H(() => (v(!0), () => g.current.abort()), []);
	async function y() {
		if (!a) {
			_.current++, o(!0), u(""), p("");
			try {
				await K("/api/scraping/cover", { code: r }, "POST", g.current.signal), await v();
			} catch (e) {
				g.current.signal.aborted || (o(!1), u(W(e)));
			}
		}
	}
	return t ? /* @__PURE__ */ q("div", {
		role: "alert",
		dangerouslySetInnerHTML: { __html: d(t, { variant: "error" }) }
	}) : /* @__PURE__ */ q("div", {
		class: "scraping-page",
		children: [
			/* @__PURE__ */ q("p", { children: "高清图片可能需要代理才能下载，请先检查连接。" }),
			/* @__PURE__ */ q("section", {
				class: "cleanupfieldset scraping-source",
				"data-geist-fieldset": !0,
				children: /* @__PURE__ */ q("div", {
					class: "geist-fieldset-content scraping-fields",
					children: [
						/* @__PURE__ */ q("div", { dangerouslySetInnerHTML: { __html: c("scraping-cover", "高清封面") } }),
						/* @__PURE__ */ q("form", {
							class: "scraping-cover-form",
							onSubmit: (e) => {
								e.preventDefault(), y();
							},
							children: [/* @__PURE__ */ q("input", {
								class: "geist-input",
								"aria-label": "馆藏番号",
								required: !0,
								value: r,
								disabled: a,
								placeholder: "输入馆藏番号，如 ABW-232",
								onInput: (e) => i(e.currentTarget.value)
							}), /* @__PURE__ */ q("button", {
								ref: m,
								class: "geist-button primary",
								type: "submit",
								children: "抓取封面"
							})]
						}),
						a && /* @__PURE__ */ q("div", {
							"aria-live": "polite",
							dangerouslySetInnerHTML: { __html: l("正在抓取封面") }
						}),
						s && /* @__PURE__ */ q("div", {
							role: "alert",
							dangerouslySetInnerHTML: { __html: d(s, { variant: "error" }) }
						}),
						f && /* @__PURE__ */ q("div", {
							role: "status",
							dangerouslySetInnerHTML: { __html: d(f) }
						})
					]
				})
			}),
			e?.sources.map((e) => /* @__PURE__ */ q(In, {
				source: e,
				toast: n
			}, e.source))
		]
	});
}
//#endregion
//#region src/review-evidence.ts
var Rn = (e = "") => /^https?:\/\//i.test(e) ? e : "";
function zn(t = "") {
	let n = Rn(t) || (t.startsWith("/") && !t.startsWith("//") ? t : "");
	return `<div class="reviewimage" data-review-picture><span class="reviewimageempty"${n ? " hidden" : ""}>未取得来源图片</span>${n ? `<img src="${e(n)}" alt="来源候选图片" loading="lazy">` : ""}</div>`;
}
function Bn(t) {
	let n = Rn(t.profile_url), r = (t.preview_assets || []).slice(0, 6), i = Math.max(0, Number(t.video_count || t.videos || 0));
	return `<section class="reviewidentityevidence"><h5>候选身份：${e(t.babepedia_name || "未标注")}</h5>
    <div class="reviewevidenceactions">${n ? `<a class="geist-button externallink" href="${e(n)}" target="_blank" rel="noopener noreferrer">来源资料<svg class="externalmark" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-external-link" /></svg></a>` : ""}
    <button type="button" class="geist-button" data-entity-kind="creator" data-entity-name="${e(t.creator || "")}">查看全部 ${i.toLocaleString()} 部作品</button></div>
    ${zn(t.preview_url)}
    <p>通过后记录身份判断。</p>
    ${r.length ? `<h5>本地作品样本</h5><div class="reviewevidencesamples">${r.map((t) => `<div class="reviewevidencesample">
      <button class="geist-button" type="button" data-review-open-item="${t.id}"><span data-middle-truncate title="${e(t.name)}">${e(t.name)}</span></button>
      <button class="geist-button" type="button" data-review-reveal="${t.id}" aria-label="打开 ${e(t.name)} 的文件位置">文件位置</button>
    </div>`).join("")}</div>` : "<p>暂无本地作品样本，打开全部作品核对。</p>"}</section>`;
}
function Vn(e) {
	for (let t of e.querySelectorAll("[data-review-picture] img")) {
		let e = () => {
			t.hidden = !0;
			let e = t.parentElement?.querySelector(".reviewimageempty");
			e && (e.hidden = !1);
		};
		t.addEventListener("error", e), t.complete && !t.naturalWidth && e();
	}
}
//#endregion
//#region src/selection.ts
function Hn(e, t, n, r, i, a = i || !e.has(r)) {
	let o = n === null ? -1 : t.indexOf(n), s = t.indexOf(r);
	return i && o >= 0 && s >= 0 ? t.slice(Math.min(o, s), Math.max(o, s) + 1).forEach((t) => e.add(t)) : a ? e.add(r) : e.delete(r), r;
}
function Un(e, t) {
	let n = t.filter((t) => e.has(t)).length;
	return {
		count: n,
		all: n > 0 && n === t.length,
		mixed: n > 0 && n < t.length
	};
}
function Wn(e, t, n) {
	t.forEach((t) => n ? e.add(t) : e.delete(t));
}
function Gn({ count: e, label: t, all: n, summary: r, actions: i, locked: a = !1 }) {
	e && (e.textContent = t), n && (n.checked = r.all, n.indeterminate = r.mixed);
	for (let e of i) e.disabled = !r.count || a;
}
//#endregion
//#region src/review-bulk.ts
var Kn = () => ({
	busy: !1,
	category: "",
	filter: "",
	groupBy: "candidates",
	anchor: null,
	selected: /* @__PURE__ */ new Set(),
	choices: /* @__PURE__ */ new Map(),
	assets: /* @__PURE__ */ new Map(),
	errors: /* @__PURE__ */ new Map()
});
function qn(e) {
	let t = e?.querySelector(".reviewbulktoolbar");
	if (!e || e.classList.contains("review-skeleton") || !t || t.offsetParent === null) return;
	e.style.setProperty("--review-controls-height", `${t.getBoundingClientRect().height}px`);
	let n = [t, ...e.querySelectorAll(".reviewgroupbar")];
	for (let e of n) {
		let t = parseFloat(getComputedStyle(e).top);
		e.classList.toggle("is-stuck", e.offsetParent !== null && window.scrollY > 0 && Number.isFinite(t) && Math.abs(e.getBoundingClientRect().top - t) <= 1);
	}
	let r = n.filter((e) => e.classList.contains("is-stuck"));
	e.classList.toggle("review-is-stuck", r.length > 0);
	let i = t, a = n.slice(1).find((e) => e.offsetParent !== null && Math.abs(e.getBoundingClientRect().top - t.getBoundingClientRect().bottom) <= 2) || t;
	e.classList.add("review-has-pane"), n.forEach((e) => e.classList.toggle("review-pane-member", e === i || e === a));
	let o = i.getBoundingClientRect(), s = a.getBoundingClientRect();
	e.style.setProperty("--review-pane-top", `${o.top}px`), e.style.setProperty("--review-pane-left", `${o.left}px`), e.style.setProperty("--review-pane-width", `${o.width}px`), e.style.setProperty("--review-pane-height", `${s.bottom - o.top}px`);
}
function Jn(e, t) {
	let n = [[
		"candidates",
		t ? "按候选数量" : "全部待复核",
		"list-filter"
	]];
	return e.some((e) => e.source || e.candidates?.some((e) => e.source)) && n.push([
		"source",
		"按来源",
		"list-filter"
	]), e.some((e) => e.field) && n.push([
		"field",
		"按字段",
		"list-filter"
	]), n;
}
function Yn(e, t) {
	let n = /* @__PURE__ */ new Map();
	for (let r of e) {
		let e, i;
		if (t === "field") e = r.field || "__unspecified_field", i = r.field_label || r.field || "未标注字段";
		else if (t === "source") {
			let t = [...new Set((r.candidates?.map((e) => e.source || "") || [r.source || ""]).filter(Boolean))].sort();
			e = JSON.stringify(t), i = t.join(" / ") || "未标注来源";
		} else e = r.candidates ? r.candidates.length === 1 ? "single" : "multiple" : "pending", i = e === "single" ? "单一候选" : e === "multiple" ? "需选择来源" : "待复核";
		n.has(e) || n.set(e, {
			key: e,
			title: i,
			rows: []
		}), n.get(e).rows.push(r);
	}
	return [...n.values()];
}
function Xn(e, t, n, r, i) {
	e.anchor = Hn(e.selected, t, e.anchor, n, r, i);
}
async function Zn(e, t, n, r) {
	let i = [], a = 0;
	for (let o of e) {
		if (!r()) break;
		try {
			let e = await t(o.payload);
			if (!e.ok) throw Error(e.error || "服务端未采用该项");
			a++, n(o.key);
		} catch (e) {
			i.push({
				key: o.key,
				message: W(e)
			});
		}
	}
	return {
		completed: a,
		failures: i
	};
}
function Qn(e) {
	return e.length ? [...new Set(e.flatMap((e) => e.candidates?.map((e) => e.source || "") || []))].filter((t) => t && e.every((e) => e.candidates?.filter((e) => e.source === t).length === 1)) : [];
}
function $n(e, n) {
	let r = e.querySelector(".reviewlist");
	if (!r || !n.rows.length || n.locked) return;
	let i = n.state, a = [...r.querySelectorAll("[data-review-key]")];
	n.category !== void 0 && i.category !== n.category && (i.category = n.category, i.filter = "", i.groupBy = "candidates", i.anchor = null);
	let s = n.catalog || n.rows, c = Jn(s, n.metadata);
	c.some((e) => e[0] === i.groupBy) || (i.groupBy = "candidates", i.filter = "");
	let l = Yn(s, i.groupBy);
	l.some((e) => e.key === i.filter) || (i.filter = "");
	let u = () => [...r.querySelectorAll("[data-review-key]")].filter((e) => !e.closest("[hidden]")), d = () => u().filter((e) => i.selected.has(e.dataset.reviewKey)), f = () => n.rows.filter((e) => d().some((t) => t.dataset.reviewKey === e.item_key)), m = (e) => !e.querySelector("[data-review-status=\"approved\"]")?.disabled, g = (e, t = "") => {
		let n = document.createElement("button");
		return n.type = "button", n.className = `geist-button ${t}`.trim(), n.textContent = e, n;
	}, _ = document.createElement("div");
	_.className = "reviewbulkbar reviewbulktoolbar", _.setAttribute("role", "group"), _.setAttribute("aria-label", "复核批量操作");
	let y = document.createElement("div");
	y.className = "reviewgroupby", y.innerHTML = p(c, i.groupBy, { label: "筛选分组方式" });
	let b = v(y.firstElementChild);
	y.querySelectorAll("[data-select-option] .gselectmark").forEach((e) => e.remove()), b.addEventListener("change", () => {
		if (i.busy || !c.some((e) => e[0] === b.value)) return;
		i.groupBy = b.value, i.filter = "", i.anchor = null;
		let t = e.parentElement;
		n.refresh(), t?.querySelector(".reviewgroupby button")?.focus({ preventScroll: !0 });
	});
	let x = document.createElement("div");
	x.className = "reviewcategoryfilter", x.hidden = l.length < 2, x.innerHTML = p([[
		"",
		"全部分类",
		"list-filter"
	], ...l.map((e) => [
		e.key,
		`${e.title} · ${e.rows.length}`,
		"list-filter"
	])], i.filter, { label: i.groupBy === "field" ? "筛选字段分类" : "筛选当前分类" });
	let S = x.querySelector("[data-select-menu]");
	if (S) {
		let e = document.createElement("div");
		e.setAttribute("role", "group"), e.setAttribute("aria-label", i.groupBy === "field" ? "字段分类" : "当前分类");
		let t = document.createElement("div");
		t.className = "reviewfilterheading", t.textContent = e.getAttribute("aria-label"), t.setAttribute("aria-hidden", "true"), e.append(t, ...Array.from(S.children).slice(1)), S.append(e);
	}
	let C = v(x.firstElementChild);
	x.querySelectorAll("[data-select-option] .gselectmark").forEach((e) => e.remove()), C.addEventListener("change", () => {
		if (i.busy || C.value && !l.some((e) => e.key === C.value)) return;
		i.filter = C.value, i.anchor = null;
		let t = e.parentElement;
		n.refresh(), t?.querySelector(".reviewcategoryfilter button")?.focus({ preventScroll: !0 });
	});
	let w = g("全选本页"), T = g("通过所选", "primary"), E = g("拒绝所选", "error"), D = document.createElement("span");
	D.className = "reviewselectedcount selectiondockcount", D.setAttribute("role", "status");
	let O = document.createElement("div");
	O.className = "reviewbulksource", O.hidden = !n.metadata;
	let k = document.createElement("p");
	k.className = "reviewstate reviewbulkfeedback", k.setAttribute("role", "status");
	let A = document.createElement("div");
	A.className = "reviewbulkdecisions", A.append(T, E);
	let j = document.createElement("div");
	j.className = "selectiondock reviewdock", j.setAttribute("role", "group"), j.setAttribute("aria-label", "复核所选项目");
	let ee = g("取消选择");
	j.append(D, O, A, ee, k), _.append(y, x, w);
	let te = e.querySelector(".reviewcontrols");
	te ? te.after(_) : r.before(_), e.append(j), r.classList.add("reviewgroups");
	let M = () => {
		i.selected.clear(), i.anchor = null, P();
	};
	ee.onclick = () => {
		i.busy || (M(), w.focus({ preventScroll: !0 }));
	}, w.onclick = () => {
		if (i.busy) return;
		let e = u(), t = d().length === e.length;
		e.forEach((e) => t ? i.selected.delete(e.dataset.reviewKey) : i.selected.add(e.dataset.reviewKey)), P();
	}, T.onclick = () => re("approved", T), E.onclick = () => re("rejected", E);
	let ne = [];
	for (let e of l) {
		let n = e.rows.map((e) => a.find((t) => t.dataset.reviewKey === e.item_key)).filter((e) => !!e);
		if (!n.length) continue;
		let s = document.createElement("section");
		s.className = "reviewgroup", s.hidden = !!i.filter && e.key !== i.filter;
		let c = document.createElement("div");
		c.className = "reviewbulkbar reviewgroupbar";
		let l = document.createElement("h3");
		l.textContent = `${e.title} · ${n.length}`;
		let d = g("全选本组"), f = document.createElement("div");
		f.className = "reviewlist", c.append(l, d), s.append(c, f), r.append(s), d.onclick = () => {
			if (i.busy) return;
			let e = n.map((e) => e.dataset.reviewKey);
			Wn(i.selected, e, !e.every((e) => i.selected.has(e))), P();
		}, ne.push(() => {
			let e = n.every((e) => i.selected.has(e.dataset.reviewKey));
			d.innerHTML = t(e ? "check-check-outline" : "check-check") + (e ? "清空本组" : "全选本组"), d.setAttribute("aria-pressed", String(e));
		});
		for (let e of n) {
			f.append(e);
			let t = e.dataset.reviewKey;
			i.errors.has(t) && (e.querySelector(".reviewstate").textContent = i.errors.get(t));
			let n = e.querySelector("h4,.reviewentity b") || e, r = document.createElement("label");
			r.className = "reviewpickitem", r.innerHTML = o();
			let a = r.querySelector("input");
			if (a.setAttribute("aria-label", `选择 ${e.querySelector("legend")?.textContent || n.textContent || t}`), n !== e) {
				let e = document.createElement("span");
				e.className = "reviewpickname", e.append(...n.childNodes), n.classList.add("reviewpickheading"), n.append(r, e);
			} else e.prepend(r);
			let s = (e, n) => {
				Xn(i, u().map((e) => e.dataset.reviewKey), t, e, n), P();
			};
			if (r.addEventListener("mousedown", (e) => {
				e.shiftKey && e.preventDefault();
			}), r.addEventListener("click", (e) => {
				e.target !== a && (e.preventDefault(), i.busy || (a.focus(), s(e.shiftKey, !a.checked)));
			}), a.addEventListener("click", (e) => {
				i.busy || s(e.shiftKey, a.checked);
			}), a.addEventListener("keydown", (n) => {
				if (!(i.busy || !n.shiftKey)) {
					if (n.key === " ") n.preventDefault(), s(!0, !0);
					else if (n.key === "ArrowDown" || n.key === "ArrowUp") {
						n.preventDefault();
						let r = u(), a = r[r.indexOf(e) + (n.key === "ArrowDown" ? 1 : -1)];
						a && (i.anchor === null && (i.anchor = t), Xn(i, r.map((e) => e.dataset.reviewKey), a.dataset.reviewKey, !0, !0), P(), a.querySelector(".reviewpickitem input")?.focus());
					}
				}
			}), ne.push(() => {
				a.checked = i.selected.has(t);
			}), i.assets.has(t)) {
				let n = i.assets.get(t), r = [...e.querySelectorAll("[data-review-asset]")];
				r.forEach((e) => {
					let t = n.includes(Number(e.dataset.reviewAsset));
					e.setAttribute("aria-pressed", String(t)), e.classList.toggle("picked", t);
				});
				let a = e.querySelector("[data-picked-count]");
				a && (a.textContent = `已选 ${n.length} / ${r.length}`);
			}
			e.addEventListener("click", (n) => {
				n.target.closest("[data-review-asset],[data-pick-all],[data-pick-none]") && i.assets.set(t, [...e.querySelectorAll("[data-review-asset][aria-pressed=\"true\"]")].map((e) => Number(e.dataset.reviewAsset)));
			});
			for (let n of e.querySelectorAll("input[type=\"radio\"]")) i.choices.has(t) && (n.checked = i.choices.get(t) === n.value), n.addEventListener("change", () => {
				n.checked && i.choices.set(t, n.value), P();
			});
		}
	}
	e.addEventListener("keydown", (t) => {
		i.busy || !e.contains(r) || (t.key === "Escape" && i.selected.size && (t.preventDefault(), t.stopPropagation(), M()), (t.ctrlKey || t.metaKey) && t.key.toLowerCase() === "a" && !t.target.matches("textarea,input:not([type=\"checkbox\"]):not([type=\"radio\"])") && (t.preventDefault(), t.stopPropagation(), u().forEach((e) => i.selected.add(e.dataset.reviewKey)), P()));
	});
	let N = "";
	function P() {
		let e = d(), r = e.length > 0 && e.length === u().length;
		w.innerHTML = t(r ? "check-check-outline" : "check-check") + (r ? "清空当前选择" : i.filter ? "全选当前分类" : "全选本页"), w.setAttribute("aria-pressed", String(r)), j.hidden = !e.length, Gn({
			count: D,
			label: `已选 ${e.length} 项`,
			summary: Un(i.selected, u().map((e) => e.dataset.reviewKey)),
			actions: [T, E]
		}), T.disabled ||= e.some((e) => !m(e));
		let a = Qn(f());
		O.hidden = !n.metadata || !f().some((e) => (e.candidates?.length || 0) > 1);
		let o = e.length && !a.length ? "所选项目无共同来源" : "统一选择来源", s = JSON.stringify([o, a]);
		if (s !== N) {
			N = s, O.innerHTML = p([["", o], ...a.map((e) => [e, e])], "", { label: "统一选择来源" });
			let e = v(O.firstElementChild);
			e.disabled = !a.length, e.addEventListener("change", () => {
				if (!(i.busy || !Qn(f()).includes(e.value))) {
					for (let t of d()) {
						let r = n.rows.find((e) => e.item_key === t.dataset.reviewKey).candidates.find((t) => t.source === e.value);
						t.querySelectorAll("input[type=\"radio\"]").forEach((e) => {
							e.checked = e.value === r.candidate_key;
						}), i.choices.set(t.dataset.reviewKey, r.candidate_key);
					}
					k.textContent = `已选择 ${e.value}，点击通过所选采用。`;
				}
			});
		}
		ne.forEach((e) => e());
	}
	async function re(t, r) {
		if (i.busy || !d().length) return;
		let a = d().map((e) => ({
			key: e.dataset.reviewKey,
			payload: {
				...n.payload(e),
				status: t
			}
		}));
		if (t === "approved" && n.metadata && a.some((e) => !e.payload.candidate_key)) {
			k.textContent = "请先为所选的多来源候选选择来源。", d().find((e) => !e.querySelector("input[type=\"radio\"]:checked"))?.querySelector("input[type=\"radio\"]")?.focus();
			return;
		}
		i.busy = !0, k.textContent = `正在处理 0 / ${a.length}`, h(r, !0);
		let o = [...e.querySelectorAll("button,input")], s = o.map((e) => e.getAttribute("aria-disabled"));
		o.forEach((e) => e.setAttribute("aria-disabled", "true"));
		let c = (e) => {
			e instanceof KeyboardEvent && e.key === "Tab" || (e.preventDefault(), e.stopImmediatePropagation());
		};
		e.addEventListener("click", c, !0), e.addEventListener("keydown", c, !0);
		let l = 0, u = await Zn(a, async (e) => {
			try {
				return await n.submit(e);
			} finally {
				l++, n.active() && (k.textContent = `正在处理 ${l} / ${a.length}`);
			}
		}, (e) => {
			i.selected.delete(e), i.errors.delete(e), n.applied(e);
		}, n.active);
		if (i.busy = !1, e.removeEventListener("click", c, !0), e.removeEventListener("keydown", c, !0), o.forEach((e, t) => {
			let n = s[t];
			n === null ? e.removeAttribute("aria-disabled") : e.setAttribute("aria-disabled", n);
		}), h(r, !1), !n.active()) return;
		n.notify(`已${t === "approved" ? "通过" : "拒绝"} ${u.completed} 项${u.failures.length ? `，${u.failures.length} 项未完成` : ""}`), u.failures.forEach((e) => i.errors.set(e.key, e.message));
		let f = e.parentElement;
		n.refresh(), f?.querySelector(".reviewbulktoolbar button")?.focus({ preventScroll: !0 });
	}
	P(), qn(e);
}
function er(e, t, n = 1) {
	let r = (e, t) => Array.from({ length: t - e + 1 }, (t, n) => e + n);
	if (n * 2 + 5 >= t) return r(1, t);
	let i = Math.max(e - n, 1), a = Math.min(e + n, t), o = i > 2, s = a < t - 2;
	return !o && s ? [
		...r(1, 3 + 2 * n),
		"…",
		t
	] : o && !s ? [
		1,
		"…",
		...r(t - (2 + 2 * n), t)
	] : [
		1,
		"…",
		...r(i, a),
		"…",
		t
	];
}
function tr(e, t) {
	return Math.max(1, Math.ceil(e / t));
}
function nr(e, t) {
	return Math.min(Math.max(1, Math.floor(e) || 1), t);
}
function rr(e, t, n) {
	if (t <= 1) return "";
	let r = er(e, t).map((t) => t === "…" ? "<li class=\"board-page-dots\" aria-hidden=\"true\">…</li>" : `<li><button type="button" class="board-page" data-page="${t}" aria-label="第 ${t} 页"${t === e ? " aria-current=\"page\"" : ""}>${t}</button></li>`).join("");
	return `<nav class="board-pagination" aria-label="${n}">
    <button type="button" class="geist-button" data-page="${e - 1}"${e <= 1 ? " disabled" : ""}><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-left"></use></svg>上一页</button>
    <ul>${r}</ul>
    <button type="button" class="geist-button" data-page="${e + 1}"${e >= t ? " disabled" : ""}>下一页<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"></use></svg></button>
  </nav>`;
}
//#endregion
//#region src/native-image.ts
function ir(e, t, n, r) {
	return e > 0 && t > 0 && e === n && t === r;
}
function ar(e, t, n, r, i = 1) {
	let a = Number.isFinite(i) && i > 0 ? i : 1;
	e /= a, t /= a;
	let o = [
		e,
		t,
		n,
		r
	].every((e) => Number.isFinite(e) && e > 0), s = o && Math.min(n, r) >= 64 && (e < n * .4 || t < r * .4), c = o ? Math.min(1, n / e, r / t) : 1;
	return {
		small: s,
		width: e * c,
		height: t * c
	};
}
//#endregion
//#region src/avatar-picker.tsx
var or = {
	gfriends: "图库",
	history: "用过的"
};
function sr({ kind: e, id: t, name: n, onPicked: r }) {
	let i = U(null), o = U(null), s = U(null), [c, l] = V(null), [u, d] = V(""), [f, p] = V(""), [m, h] = V(""), [g, _] = V(!1);
	H(() => {
		if (!g || c) return;
		let n = new AbortController();
		return G(`/api/avatar-choices?kind=${e}&id=${t}`, n.signal).then(l).catch((e) => {
			n.signal.aborted || d(W(e));
		}), () => n.abort();
	}, [
		g,
		c,
		e,
		t
	]), H(() => {
		a(o.current);
	}, [g, c]);
	let v = () => {
		_(!0), i.current?.showModal();
	}, y = () => {
		_(!1), i.current?.close();
	}, b = async (e, t) => {
		p(t), d("");
		try {
			await e(), y(), l(null), r();
		} catch (e) {
			d(W(e));
		} finally {
			p("");
		}
	}, x = (n) => b(() => K("/api/avatar-pick", {
		kind: e,
		id: t,
		ref: n.ref
	}), n.ref), S = () => b(() => K("/api/avatar-pick", {
		kind: e,
		id: t,
		url: m.trim()
	}), "url"), C = async (n) => b(async () => {
		let r = await fetch(`/api/avatar-pick?kind=${e}&id=${t}&name=${encodeURIComponent(n.name)}`, {
			method: "POST",
			credentials: "same-origin",
			body: n
		});
		if (!r.ok) {
			let e = await r.json().catch(() => null);
			throw Error(e?.error || `请求失败（${r.status}）`);
		}
	}, "file"), w = c?.choices || [], T = (c?.matched_names || []).filter((e) => e !== n), E = c ? T.length ? `${n}：图库里按「${T.join("」「")}」找到的。` : w.length ? `${n}：换上的那张留在本机，随时能换回来。` : `${n}：图库里没有这个名字，用下面两种方式换。` : "正在找可用的图…", D = !!c && c.index_stale && !w.some((e) => e.source === "gfriends");
	return /* @__PURE__ */ q("div", {
		class: "avatarpick",
		children: [/* @__PURE__ */ q("button", {
			type: "button",
			class: "avatarpick-open",
			onClick: v,
			"aria-haspopup": "dialog",
			"aria-label": `更换${n}的头像`,
			title: "更换头像",
			children: /* @__PURE__ */ q("svg", {
				viewBox: "0 0 24 24",
				"aria-hidden": "true",
				children: /* @__PURE__ */ q("use", { href: "#i-plus" })
			})
		}), /* @__PURE__ */ q("dialog", {
			ref: i,
			class: "geist-modal avatarpick-popover",
			"aria-label": "更换头像",
			onCancel: y,
			onClick: (e) => {
				e.target === i.current && y();
			},
			children: [/* @__PURE__ */ q("div", {
				class: "avatarpick-head",
				children: [
					/* @__PURE__ */ q("span", {
						class: "avatarpick-mark",
						"aria-hidden": "true",
						children: /* @__PURE__ */ q("svg", {
							viewBox: "0 0 24 24",
							children: /* @__PURE__ */ q("use", { href: "#i-user-round" })
						})
					}),
					/* @__PURE__ */ q("div", {
						class: "avatarpick-headtext",
						children: [
							/* @__PURE__ */ q("div", {
								class: "avatarpick-title",
								children: [/* @__PURE__ */ q("h3", { children: "更换头像" }), !!w.length && /* @__PURE__ */ q("span", {
									class: "geist-badge",
									children: [w.length, " 张可选"]
								})]
							}),
							/* @__PURE__ */ q("p", { children: E }),
							D && /* @__PURE__ */ q("p", {
								class: "avatarpick-note",
								children: "图库索引还没取过，只能从用过的图里选。"
							}),
							u && /* @__PURE__ */ q("p", {
								class: "avatarpick-error",
								role: "alert",
								children: u
							})
						]
					}),
					/* @__PURE__ */ q("button", {
						type: "button",
						class: "avatarpick-close",
						onClick: y,
						"aria-label": "关闭",
						children: /* @__PURE__ */ q("svg", {
							viewBox: "0 0 24 24",
							"aria-hidden": "true",
							children: /* @__PURE__ */ q("use", { href: "#i-x" })
						})
					})
				]
			}), /* @__PURE__ */ q("div", {
				class: "avatarpick-panel",
				children: [/* @__PURE__ */ q("div", {
					class: "avatarpick-gridwrap",
					children: /* @__PURE__ */ q("div", {
						class: "avatarpick-grid",
						role: "listbox",
						"aria-label": "候选头像",
						ref: o,
						children: w.map((n) => /* @__PURE__ */ q("button", {
							type: "button",
							role: "option",
							"aria-selected": n.current,
							disabled: !!f,
							class: `avatarpick-cell${n.current ? " current" : ""}`,
							title: `${or[n.source] || n.source} · ${n.label}` + (n.width ? ` · ${n.width}×${n.height}` : "") + (n.found_by ? ` · 按「${n.found_by}」找到` : ""),
							onClick: () => x(n),
							children: [
								/* @__PURE__ */ q("img", {
									loading: "lazy",
									alt: "",
									src: `/avatar-choice?kind=${e}&id=${t}&ref=${encodeURIComponent(n.ref)}`
								}),
								/* @__PURE__ */ q("span", { children: n.label }),
								n.current && /* @__PURE__ */ q("b", { children: "在用" })
							]
						}, n.ref))
					})
				}), /* @__PURE__ */ q("div", {
					class: "avatarpick-actions",
					children: [
						/* @__PURE__ */ q("button", {
							type: "button",
							class: "geist-button",
							disabled: !!f,
							onClick: () => s.current?.click(),
							children: "从本机选图片"
						}),
						/* @__PURE__ */ q("input", {
							ref: s,
							type: "file",
							accept: "image/png,image/jpeg",
							hidden: !0,
							onChange: (e) => {
								let t = e.currentTarget.files?.[0];
								e.currentTarget.value = "", t && C(t);
							}
						}),
						/* @__PURE__ */ q("div", {
							class: "avatarpick-url",
							children: [/* @__PURE__ */ q("input", {
								type: "url",
								class: "geist-input",
								value: m,
								placeholder: "https://…",
								"aria-label": "图片地址",
								onInput: (e) => h(e.currentTarget.value)
							}), /* @__PURE__ */ q("button", {
								type: "button",
								class: "geist-button",
								disabled: !m.trim() || !!f,
								onClick: S,
								children: "用这个地址"
							})]
						})
					]
				})]
			})]
		})]
	});
}
function cr(e, t) {
	Ee(/* @__PURE__ */ q(sr, { ...t }), e);
}
function lr(e) {
	Ee(null, e);
}
//#endregion
//#region src/entity-skeleton.ts
function ur(e, t, n) {
	return `<section data-skeleton="entity/${e}" role="status" aria-label="正在读取资料">
    <span class="sr-only">正在读取资料</span><div aria-hidden="true">
    <section class="entityhero"><div class="entityprofile"><div class="entityportrait ${e === "studio" || e === "agency" ? "square " : ""}skeleton"></div>
      <div class="entityidentity entityskeletontext"><div class="entitytitle"><h2 class="skeleton">&nbsp;</h2></div>
      <div class="alias"><span class="skeleton"></span></div>
      <div class="entitylinks"><span class="skeleton"></span></div></div></div></section>
    <div class="board-filter-frame" data-filter-frame>
      <section class="entitytagbar" data-filter-row="top"><div class="filterscroll" data-skeleton-tier="pill"></div></section>
      ${t}</div>
    <div class="entitysection">${n}</div></div></section>`;
}
//#endregion
//#region src/board-skeleton.ts
var X = (e = "60%") => `<span class="skeleton" style="width:${e}"></span>`, Z = () => `${X("80%")}${X("48%")}`, Q = (e, t) => e.repeat(t), dr = (e, t = "metricstrip") => `<div class="${t}">${e.map((e) => `<div class="tastesummary"><span class="board-stat-label">${e}</span><b class="board-stat-value">${X("45%")}</b><small class="board-stat-footer">${X("60%")}</small></div>`).join("")}</div>`, fr = (e, t = "skeleton-tabs") => `<div class="${t}">${e.map((e) => `<span>${e}</span>`).join("")}</div>`, pr = (e, t) => `<div class="${t} skeleton-segments" data-board-segments="true">${e.map((e, t) => `<span${t === 0 ? " class=\"skeleton-segment-selected\"" : ""}>${e}</span>`).join("")}</div>`, mr = (e) => `<section class="board-radial-card"><header><span>${e}</span><b>${X()}</b></header><div class="board-rings skeleton-rings"><span class="skeleton skeleton-ring"></span></div><div class="skeleton-lines">${Z()}</div></section>`, hr = (e) => `<section class="insightpanel"><header>${e}</header><div class="insightpanelbody skeleton-lines">${Q(Z(), 3)}</div></section>`, gr = (e) => `<button class="fbtn" type="button" disabled>${e}</button>`, _r = (e) => `<div class="fsechead" data-collapse-toolbar><h3>关注列表</h3><span class="fmeta">${X("100px")}</span><div class="followtoolbaractions"><button class="fbtn primary followcheckall" disabled>${t("refresh-cw")}<span data-collapse-label>检查全部</span></button><div class="iconswitch" data-board-segments="true"><label>${t("layout-grid")}</label><label>${t("table")}</label></div><span class="fmanagesort" data-collapse-field>${t("sort")}${p([["checked", "检查时间"]], "checked", {
	label: "关注列表排序",
	attr: "disabled"
})}</span><button class="fbtn fmanagedir" disabled>${t("arrow-down")}</button>${e ? "" : gr(t("chevron-up") + "<span data-collapse-label>全部收起</span>")}</div></div>`, vr = () => `<div class="fsource frow"><span class="fchannelcheck">${X("18px")}</span><b>${X("85%")}</b><span class="fprovider">${X("54px")}</span><span class="fmeta fchecked">${X("40px")}</span><span class="fsourceactions"><span class="skeleton skeleton-icon"></span><span class="skeleton skeleton-icon"></span></span></div>`, yr = () => `<details class="fauthor" open><summary class="fauthorhead"><span class="favatar skeleton"></span><b>${X("90px")}</b><span class="skeleton skeleton-icon"></span><span class="fmeta">${X("40px")}</span><span class="board-author-actions"><button type="button" class="fbtn small" data-follow-author-select disabled>${t("check-check")}<span data-author-select-label>全选</span></button><span class="skeleton skeleton-icon"></span></span></summary><div class="fauthorsources">${Q(vr(), 3)}</div></details>`;
function br() {
	return `<div data-skeleton="detail" role="status" aria-label="正在读取作品详情"><div class="sgrid" aria-hidden="true"><div class="vwrap skeleton-detail-media skeleton"></div><aside class="side"><div class="sidecontent skeleton-lines">${X("85%")}${X("65%")}${Q(Z(), 4)}</div></aside></div></div>`;
}
function xr(e, t = {}) {
	let n = "";
	if (e === "/stats") n = `<div class="insightpage statsdashboard"><header class="insighttoolbar">${X("38%")}</header>${dr([
		"馆藏视频",
		"看过",
		"内容标签",
		"使用空间"
	])}<section class="insightdetail"><div class="insightdetailbody"><div class="board-inventory-charts">${mr("网盘与本地")}${mr("媒体库")}</div></div></section>${hr("内容标签")}</div>`;
	else if (e === "/taste") n = `<div class="tastepage"><header class="tastehead">${pr(["浏览器记录", "Peach 内部"], "insightswitch")}${X("24%")}</header><div class="tastestate"></div>${dr([
		"浏览记录",
		"口味维度",
		"浏览候选",
		"私有导出"
	], "tastesummaries")}<section class="tastehero"><div class="insightcopy"><span>浏览器画像</span><div class="skeleton skeleton-radar"></div></div><div class="tastebars skeleton-lines">${Q(Z(), 4)}</div></section>${hr("口味分析")}<div class="board-activity-charts">${hr("浏览活动")}${hr("时间分布")}</div>${hr("标签")}</div>`;
	else if (e === "/follow-manage") {
		let e = t.followLayout === "table", r = e ? `<div class="ftableframe"><div class="ftablewrap"><table class="ftable"><thead><tr>${[
			"选择",
			"创作者",
			"来源",
			"站点",
			"状态",
			"上次检查",
			"操作"
		].map((e) => `<th>${e === "选择" ? "<label>" + o("disabled aria-label=\"全选本页来源\"") + "</label>" : e}</th>`).join("")}</tr></thead><tbody>${Q(`<tr>${[
			"20px",
			"90px",
			"120px",
			"60px",
			"40px",
			"100px",
			"60px"
		].map((e) => `<td>${X(e)}</td>`).join("")}</tr>`, 6)}</tbody></table></div></div>` : `<div class="board-follow-list">${Q(yr(), 4)}</div>`;
		n = `<div class="follow followmanage"><div class="fmanageoverview">${[
			"关注创作者",
			"启用来源",
			"检查失败",
			"未看更新"
		].map((e) => `<div><span>${e}</span><b>${X()}</b></div>`).join("")}</div>${pr([
			"关注列表",
			"添加关注",
			"来源和凭证"
		], "follow-workspace-switch")}<div class="fmain"><section class="fsec" data-follow-workspace-panel="list">${_r(e)}<div class="board-follow-selection"${e ? " hidden" : ""}><label>${o("disabled")}全选本页</label></div><div class="frows fsources" data-layout="${e ? "table" : "default"}">${r}<div class="followpagefooter"><div class="followpageinfo">${X("120px")}${X("100px")}</div></div></div></section></div></div>`;
	} else if (e === "/configuration") n = `<div class="configpage">${fr([
		"通用",
		"媒体",
		"网络与访问",
		"更新与维护"
	])}<section class="configfieldset"><div class="geist-fieldset-content"><h3 class="geist-fieldset-title">开机自启</h3><div class="skeleton-lines">${Q(`<div class="skeleton-setting">${X("35%")}<span class="skeleton skeleton-toggle"></span></div>`, 3)}</div></div><footer class="geist-fieldset-footer">${X("100px")}</footer></section></div>`;
	else if (e === "/activity") n = `<div class="activitypage">${[
		"正在进行",
		"被挡下的",
		"最近完成"
	].map((e) => `<section class="activitysection"><h3 class="geist-fieldset-title">${e}</h3><div class="activity-runs"><article class="cleanupfieldset activity-run"><div class="geist-fieldset-content skeleton-lines">${X("35%")}${Z()}</div></article></div></section>`).join("")}</div>`;
	else if (e === "/duplicates") n = `<div class="review"><div class="collection-summary">${X("38%")}</div><div class="fsechead dupactions"><h3>批量保留</h3>${X("40%")}</div>${Q(`<section class="dupgroup"><div class="duphead">${X("45%")}</div><div class="duplist">${Q(`<div class="duprow"><span class="dupcover skeleton"></span><span class="dupmarks">${X()}</span><span class="dupname">${X("90%")}</span>${X()}${X()}${X()}<span class="duppath">${X("70%")}</span></div>`, 2)}</div></section>`, 2)}</div>`;
	else if (e === "/quality-goals") n = `<div class="quality-workspace"><div class="collection-summary"><strong>待升级</strong>${X("20%")}</div><div class="qualitylist">${Q(`<article class="qualityitem"><span class="qualitycover skeleton"></span><div class="qualitybody skeleton-lines">${Z()}</div><footer class="qualityactions">${X("80%")}</footer></article>`, 6)}</div></div>`;
	else if (e === "/playlists") n = `<section class="playlistpage"><header><div><h2>播放列表</h2><p>保存 Mix，按自己的顺序继续播放。</p></div><div class="playlistcreate skeleton-lines"><span>新播放列表</span>${X("200px")}</div></header><div class="playlistcards">${Q(`<article class="card playlistcard"><div class="mixstack"><div class="pic skeleton"></div></div><div class="mixmeta"><span class="mav skeleton"></span><div class="mixcopy skeleton-lines">${Z()}</div></div></article>`, 6)}</div></section>`;
	else return "";
	return `<div class="board-page-skeleton" data-skeleton="board${e}" role="status" aria-label="正在读取页面"><div aria-hidden="true" inert>${n}</div></div>`;
}
//#endregion
//#region src/catalog-onboarding.ts
var Sr = [
	"loc",
	"creator",
	"performer",
	"studio",
	"series",
	"agency",
	"tag",
	"tag_match",
	"len",
	"dur_min",
	"dur_max",
	"orient",
	"region",
	"state",
	"jav",
	"thumb"
];
function Cr() {
	let e = (e) => Array(64).fill(e).join("");
	return {
		tiers: "<div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"av\"><span class=\"ring\"></span><span class=\"nm\">&nbsp;</span></span>") + "</div><div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"brandpill\"><span class=\"mk\"></span><span class=\"placeholder-name\">&nbsp;</span></span>") + "</div>",
		tags: "<span class=\"catalog-placeholder placeholder-tags\" aria-hidden=\"true\">" + e("<span class=\"pill\">&nbsp;</span>") + "</span>"
	};
}
async function wr(e, t) {
	let n = new URLSearchParams();
	for (let t of Sr) e[t] && n.set(t, e[t]);
	let [r, i] = await Promise.all([t("/api/facets?" + n), t("/api/items?" + n + "&limit=5")]), a = [...new Set([
		...r.creators || [],
		...r.tagperformers || [],
		...r.tags || []
	].map((e) => String(e.k || "")).concat((i.items || []).map((e) => e.code || e.name || "")))].filter((e) => e.length > 1).slice(0, 10);
	return (await Promise.all(a.map(async (e) => {
		let r = new URLSearchParams(n);
		return r.set("q", e), r.set("limit", "1"), (await t("/api/items?" + r)).total > 0 ? e : "";
	}))).filter(Boolean);
}
function Tr({ kind: e = "catalog", filtered: t = !1, jav: n = !1, configurable: r = !1, online: i = !1 } = {}) {
	let a = r ? "<button class=\"geist-button primary\" data-empty-settings>添加内容</button>" : "", o = "<a class=\"geist-button" + (!r || i ? " primary" : "") + "\" href=\"/follow-manage?tab=add\">添加关注</a>";
	if (t || n) return s("search", n ? "还没有符合条件的 JAV 作品" : "没有符合条件的内容", n ? "已扫描但尚未补充发行资料的视频可在全部内容中查看。" : "清除筛选或搜索条件后查看全部内容。", { actions: "<a class=\"geist-button primary\" href=\"/?loc=&thumb=0\">查看全部内容</a>" });
	if (e !== "catalog") {
		let t = (i ? {
			tags: "标签",
			performers: "创作者"
		}[e] : "") || {
			tags: "标签",
			performers: "艺人",
			creators: "创作者",
			studios: "厂牌",
			agencies: "事务所",
			series: "系列"
		}[e] || "资料";
		return s(e === "tags" ? "tags" : "user-round", "还没有" + t, i ? "添加关注来源并获取内容后，这里会显示来源上的" + t + "。" : "添加内容并补充资料后，这里会显示对应信息。", { actions: i ? o : a + o });
	}
	return s("play", "还没有视频", "添加媒体文件夹或关注来源，开始建立你的馆藏。", { actions: a + o });
}
//#endregion
//#region src/sidebar.ts
function Er(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function Dr(e, t) {
	return e.dataset.surface?.split("?")[0] === t.split("?")[0] && e.querySelector(".dnav") ? (e.dataset.surface = t, !1) : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function Or(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/resource-sync.ts
var $ = (e = 0) => Number(e).toLocaleString(), kr = {
	local: "本地磁盘",
	115: "115",
	pikpak: "PikPak"
}, Ar = (e) => m(i[e] ?? "database"), jr = (e, t, n) => `<article class="board-plain-stat resourcestat">
    <span class="board-plain-stat-head">${e}</span>
    <strong>${t}</strong>
    <span class="cleanupmeta">${n}</span></article>`;
function Mr(e, t) {
	let n = e.cache || {
		files: 0,
		bytes: 0
	}, r = !!(e.missing || n.files);
	return `<div class="cleanupstats resourcestats">${(e.sources || []).map((e) => jr(`<span class="board-stat-tile resourcestat-tile">${Ar(e.location)}</span>${kr[e.location] || "媒体来源"}<span class="resourcestat-state ${e.online ? "online" : "offline"}">${e.online ? "可访问" : "离线，已跳过"}</span>`, e.online ? `${$(e.missing)} 项` : "—", [e.online ? `找不到文件 · 已检查 ${$(e.checked)} 项` : `馆藏中有 ${$(e.total)} 项`, e.unreadable ? `${$(e.unreadable)} 项读取失败，已跳过` : ""].filter(Boolean).join(" · "))).join("")}
    ${jr("待移入回收站", `${$(e.missing)} 项`, "")}
    ${jr("可清理的缓存", `${$(n.files)} 个`, n.files ? t(n.bytes) : "")}</div>
    ${r ? d(`将把找不到文件的 ${$(e.missing)} 项馆藏记录移入回收站，并清理 ${$(n.files)} 个闲置缓存。`, { label: "清理内容" }) : ""}
    <div class="resourceapplyrow geist-fieldset-footer" data-geist-fieldset-footer>${r ? "<button class=\"geist-button primary\" type=\"button\" id=\"resourceApply\">清理失效记录与缓存</button>" : "<p class=\"resourcesyncok\">已检查可访问的来源，没有待清理的记录或缓存。</p>"}</div>`;
}
//#endregion
//#region src/jav-artwork.ts
function Nr(e) {
	return [
		"small",
		"sleeve",
		"preview"
	].includes(String(e)) ? "small" : "big";
}
function Pr(e) {
	return {
		javLayout: Nr(e.javLayout),
		javImage: Fr(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function Fr(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function Ir(e, t) {
	return e.is_jav && e.code && e.has_cover && (Fr(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function Lr(e, t) {
	let n = Number(e?.px?.[0]), r = Number(e?.px?.[1]), i = Number(e?.x0);
	if (!(n > 0 && r > 0 && t > 0) || !Number.isFinite(i)) return null;
	let a = Math.min(1, Math.max(0, i / n)), o = n / r / t, s = (1 - a) * o;
	if (!(s > 0)) return null;
	let c = s <= 1 ? (1 - s) / 2 - a * o : 1 - o, l = (e) => Math.round(e * 1e4) / 100;
	return {
		clip: l(a),
		left: l(c)
	};
}
function Rr(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (Fr(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.classList.remove("panel"), e.removeAttribute("style"), e.closest(".pic")?.style.removeProperty("--cover-blur"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
//#endregion
//#region src/islands.ts
var zr = {
	"library-processing": {
		load: ft,
		component: bt
	},
	scraping: {
		load: Pn,
		component: Ln
	},
	"quality-goals": { react: "quality-goals" },
	configuration: {
		load: Mn,
		component: Nn
	},
	activity: { react: "activity" }
}, Br = () => Object.keys(zr), Vr = /* @__PURE__ */ new Map();
async function Hr(e, t, n, r = {}) {
	let i = zr[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	Kr(t);
	let a = {
		controller: new AbortController(),
		painted: !1
	};
	if (Vr.set(t, a), "react" in i) return Wr(i, t, n, a, r);
	let o;
	try {
		o = {
			data: await i.load(n, a.controller.signal),
			error: ""
		};
	} catch (e) {
		if (a.controller.signal.aborted) return;
		o = {
			data: null,
			error: W(e)
		};
	}
	if (!Ur(t, a, r)) return;
	let s = {
		...n,
		...o
	};
	Ee(ie(i.component, s), t);
}
function Ur(e, t, n) {
	return Vr.get(e) === t ? n.isCurrent && !n.isCurrent() ? (Vr.delete(e), !1) : (e.textContent = "", t.painted = !0, !0) : !1;
}
async function Wr(e, t, n, r, i) {
	let a = (await import("/dist/peach-react.js")).pages[e.react];
	try {
		await a.prefetch(n, r.controller.signal);
	} catch {
		if (r.controller.signal.aborted) return;
	}
	if (!Ur(t, r, i)) return;
	let o = t.ownerDocument.createElement("div");
	o.className = "peach-react", t.append(o);
	let s = a.mount(o, n);
	r.dispose = () => {
		s.unmount(), o.remove();
	};
}
var Gr = (e) => !!e && Vr.has(e);
function Kr(e) {
	let t = Vr.get(e);
	t && (t.controller.abort(), Vr.delete(e), t.dispose ? t.dispose() : t.painted && Ee(null, e));
}
//#endregion
export { Tt as TASTE_GUIDE_KEY, Cn as activityChartsHtml, xr as boardPageSkeleton, ke as boundedPreference, Tr as catalogEmptyHtml, wr as catalogSuggestions, nr as clampPage, Ct as cleanupSkeletonHtml, xt as cloudLocations, St as cloudPreferenceLocations, Kn as createReviewSelection, _n as creatorSankeyHtml, br as detailSkeletonHtml, Pe as distributionChart, Cr as emptyCatalogLayout, ur as entitySkeletonHtml, ct as followJobProgress, Yn as groupReviewRows, Bn as identityEvidenceHtml, jt as initBoardControls, Gr as islandMounted, Br as islandNames, Ir as javImageKind, ot as jobActivityHtml, Ne as jobProgressHtml, ir as matchesFaceSource, cr as mountAvatarPicker, kt as mountBoardStatePreview, Hr as mountIsland, je as mountNumberSetting, ar as nativeImageFit, Fr as normalizeJavImage, Nr as normalizeJavLayout, Pr as normalizeJavPreferences, tr as pageCount, rr as paginationHtml, Lr as panelFrame, De as preferredDirection, Ie as radarChart, bn as radialCardHtml, Fe as rankedChart, Mr as resourceScanHtml, zn as reviewImageHtml, Wn as selectGroup, Hn as selectRange, Un as selectionSummary, Er as sidebarHasCatalogContent, En as sidebarSectionHtml, Or as sidebarTagCounts, Me as statCardBody, At as syncBoardRange, Rr as syncJavImages, Ae as syncNumberSetting, Gn as syncSelectionToolbar, Dr as syncSidebarSurface, wt as tasteHistoryGuideHtml, kn as transitionTheme, lr as unmountAvatarPicker, Kr as unmountIsland, qn as updateReviewSticky, st as watchJob, wn as wireActivityCharts, vn as wireCreatorSankey, Lt as wireExpandableRanks, It as wireGrowingCharts, xn as wireRadialCards, Vn as wireReviewPictures, $n as wireReviewSelection, Dn as wireSidebarGroups, Et as wireTasteHistoryGuide };
