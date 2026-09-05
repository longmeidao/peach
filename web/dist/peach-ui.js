import { emptyStateHtml as e, fieldsetTitle as t, noteHtml as n, selectFieldHtml as r, setActionBusy as i, wireSelectField as a } from "/js/ui-components.js";
import { LOC as o, fmtDur as s, fmtSize as c } from "/js/core.js";
//#region node_modules/preact/dist/preact.module.js
var l, u, d, f, p, m, h, g, _, v, y, b, x, S, C, w = {}, T = [], E = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, D = Array.isArray;
function O(e, t) {
	for (var n in t) e[n] = t[n];
	return e;
}
function k(e) {
	e && e.parentNode && e.parentNode.removeChild(e);
}
function A(e, t, n) {
	var r, i, a, o = {};
	for (a in t) a == "key" ? r = t[a] : a == "ref" ? i = t[a] : o[a] = t[a];
	if (arguments.length > 2 && (o.children = arguments.length > 3 ? l.call(arguments, 2) : n), typeof e == "function" && e.defaultProps != null) for (a in e.defaultProps) o[a] === void 0 && (o[a] = e.defaultProps[a]);
	return j(e, o, r, i, null);
}
function j(e, t, n, r, i) {
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
		__v: i ?? ++d,
		__i: -1,
		__u: 0
	};
	return i == null && u.vnode != null && u.vnode(a), a;
}
function M(e) {
	return e.children;
}
function N(e, t) {
	this.props = e, this.context = t;
}
function P(e, t) {
	if (t == null) return e.__ ? P(e.__, e.__i + 1) : null;
	for (var n; t < e.__k.length; t++) if ((n = e.__k[t]) != null && n.__e != null) return n.__e;
	return typeof e.type == "function" ? P(e) : null;
}
function ee(e) {
	if (e.__P && e.__d) {
		var t = e.__v, n = t.__e, r = [], i = [], a = O({}, t);
		a.__v = t.__v + 1, u.vnode && u.vnode(a), de(e.__P, a, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, r, n ?? P(t), !!(32 & t.__u), i), a.__v = t.__v, a.__.__k[a.__i] = a, pe(r, a, i), t.__e = t.__ = null, a.__e != n && te(a);
	}
}
function te(e) {
	if ((e = e.__) != null && e.__c != null) return e.__e = e.__c.base = null, e.__k.some(function(t) {
		if (t != null && t.__e != null) return e.__e = e.__c.base = t.__e;
	}), te(e);
}
function ne(e) {
	(!e.__d && (e.__d = !0) && p.push(e) && !re.__r++ || m != u.debounceRendering) && ((m = u.debounceRendering) || h)(re);
}
function re() {
	try {
		for (var e, t = 1; p.length;) p.length > t && p.sort(g), e = p.shift(), t = p.length, ee(e);
	} finally {
		p.length = re.__r = 0;
	}
}
function ie(e, t, n, r, i, a, o, s, c, l, u) {
	var d, f, p, m, h, g, _ = r && r.__k || T, v = t.length;
	for (c = ae(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || w, p.__i = d, g = de(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && ge(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = oe(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
	return n.__e = h, c;
}
function ae(e, t, n, r, i) {
	var a, o, s, c, l, u = n.length, d = u, f = 0;
	for (e.__k = Array(i), a = 0; a < i; a++) (o = t[a]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[a] = j(null, o, null, null, null) : D(o) ? o = e.__k[a] = j(M, { children: o }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[a] = j(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[a] = o, c = a + f, o.__ = e, o.__b = e.__b + 1, s = null, (l = o.__i = se(o, n, c, d)) != -1 && (d--, (s = n[l]) && (s.__u |= 2)), s == null || s.__v == null ? (l == -1 && (i > u ? f-- : i < u && f++), typeof o.type != "function" && (o.__u |= 4)) : l != c && (l == c - 1 ? f-- : l == c + 1 ? f++ : (l > c ? f-- : f++, o.__u |= 4))) : e.__k[a] = null;
	if (d) for (a = 0; a < u; a++) (s = n[a]) != null && !(2 & s.__u) && (s.__e == r && (r = P(s)), _e(s, s));
	return r;
}
function oe(e, t, n) {
	var r, i;
	if (typeof e.type == "function") {
		for (r = e.__k, i = 0; r && i < r.length; i++) r[i] && (r[i].__ = e, t = oe(r[i], t, n));
		return t;
	}
	e.__e != t && (t && e.type && !t.parentNode && (t = P(e)), t = n.insertBefore(e.__e, t || null));
	do
		t &&= t.nextSibling;
	while (t != null && t.nodeType == 8);
	return t;
}
function se(e, t, n, r) {
	var i, a, o, s = e.key, c = e.type, l = t[n], u = l != null && !(2 & l.__u);
	if (l === null && s == null || u && s == l.key && c == l.type) return n;
	if (r > +!!u) {
		for (i = n - 1, a = n + 1; i >= 0 || a < t.length;) if ((l = t[o = i >= 0 ? i-- : a++]) != null && !(2 & l.__u) && s == l.key && c == l.type) return o;
	}
	return -1;
}
function ce(e, t, n) {
	t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || E.test(t) ? n : n + "px";
}
function le(e, t, n, r, i) {
	var a, o;
	n: if (t == "style") {
		if (typeof n == "string") e.style.cssText = n;
		else {
			if (typeof r == "string" && (e.style.cssText = r = ""), r) for (t in r) n && t in n || ce(e.style, t, "");
			if (n) for (t in n) r && n[t] == r[t] || ce(e.style, t, n[t]);
		}
	} else if (t[0] == "o" && t[1] == "n") a = t != (t = t.replace(b, "$1")), o = t.toLowerCase(), t = o in e || t == "onFocusOut" || t == "onFocusIn" ? o.slice(2) : t.slice(2), e.l ||= {}, e.l[t + a] = n, n ? r ? n[y] = r[y] : (n[y] = x, e.addEventListener(t, a ? C : S, a)) : e.removeEventListener(t, a ? C : S, a);
	else {
		if (i == "http://www.w3.org/2000/svg") t = t.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
		else if (t != "width" && t != "height" && t != "href" && t != "list" && t != "form" && t != "tabIndex" && t != "download" && t != "rowSpan" && t != "colSpan" && t != "role" && t != "popover" && t in e) try {
			e[t] = n ?? "";
			break n;
		} catch {}
		typeof n == "function" || (n == null || !1 === n && t[4] != "-" ? e.removeAttribute(t) : e.setAttribute(t, t == "popover" && n == 1 ? "" : n));
	}
}
function ue(e) {
	return function(t) {
		if (this.l) {
			var n = this.l[t.type + e];
			if (t[v] == null) t[v] = x++;
			else if (t[v] < n[y]) return;
			return n(u.event ? u.event(t) : t);
		}
	};
}
function de(e, t, n, r, i, a, o, s, c, l) {
	var d, f, p, m, h, g, _, v, y, b, x, S, C, w, E, A, j = t.type;
	if (t.constructor !== void 0) return null;
	128 & n.__u && (c = !!(32 & n.__u), a = [s = t.__e = n.__e]), (d = u.__b) && d(t);
	n: if (typeof j == "function") {
		f = o.length;
		try {
			if (y = t.props, b = j.prototype && j.prototype.render, x = (d = j.contextType) && r[d.__c], S = d ? x ? x.props.value : d.__ : r, n.__c ? v = (p = t.__c = n.__c).__ = p.__E : (b ? t.__c = p = new j(y, S) : (t.__c = p = new N(y, S), p.constructor = j, p.render = ve), x && x.sub(p), p.state || (p.state = {}), p.__n = r, m = p.__d = !0, p.__h = [], p._sb = []), b && p.__s == null && (p.__s = p.state), b && j.getDerivedStateFromProps != null && (p.__s == p.state && (p.__s = O({}, p.__s)), O(p.__s, j.getDerivedStateFromProps(y, p.__s))), h = p.props, g = p.state, p.__v = t, m) b && j.getDerivedStateFromProps == null && p.componentWillMount != null && p.componentWillMount(), b && p.componentDidMount != null && p.__h.push(p.componentDidMount);
			else {
				if (b && j.getDerivedStateFromProps == null && y !== h && p.componentWillReceiveProps != null && p.componentWillReceiveProps(y, S), t.__v == n.__v || !p.__e && p.shouldComponentUpdate != null && !1 === p.shouldComponentUpdate(y, p.__s, S)) {
					t.__v != n.__v && (p.props = y, p.state = p.__s, p.__d = !1), t.__e = n.__e, t.__k = n.__k, t.__k.some(function(e) {
						e && (e.__ = t);
					}), T.push.apply(p.__h, p._sb), p._sb = [], p.__h.length && o.push(p), s = P(n);
					break n;
				}
				p.componentWillUpdate != null && p.componentWillUpdate(y, p.__s, S), b && p.componentDidUpdate != null && p.__h.push(function() {
					p.componentDidUpdate(h, g, _);
				});
			}
			if (p.context = S, p.props = y, p.__P = e, p.__e = !1, C = u.__r, w = 0, b) p.state = p.__s, p.__d = !1, C && C(t), d = p.render(p.props, p.state, p.context), T.push.apply(p.__h, p._sb), p._sb = [];
			else do
				p.__d = !1, C && C(t), d = p.render(p.props, p.state, p.context), p.state = p.__s;
			while (p.__d && ++w < 25);
			p.state = p.__s, p.getChildContext != null && (r = O(O({}, r), p.getChildContext())), b && !m && p.getSnapshotBeforeUpdate != null && (_ = p.getSnapshotBeforeUpdate(h, g)), E = d != null && d.type === M && d.key == null ? me(d.props.children) : d, s = ie(e, D(E) ? E : [E], t, n, r, i, a, o, s, c, l), p.base = t.__e, t.__u &= -161, p.__h.length && o.push(p), v && (p.__E = p.__ = null);
		} catch (e) {
			if (o.length = f, t.__v = null, c || a != null) {
				if (e.then) {
					for (t.__u |= c ? 160 : 128; s && s.nodeType == 8 && s.nextSibling;) s = s.nextSibling;
					a != null && (a[a.indexOf(s)] = null), t.__e = s;
				} else if (a != null) for (A = a.length; A--;) k(a[A]);
			} else t.__e = n.__e;
			t.__k ??= n.__k || [], e.then || fe(t), u.__e(e, t, n);
		}
	} else a == null && t.__v == n.__v ? (t.__k = n.__k, t.__e = n.__e) : s = t.__e = he(n.__e, t, n, r, i, a, o, c, l);
	return (d = u.diffed) && d(t), 128 & t.__u ? void 0 : s;
}
function fe(e) {
	e && (e.__c && (e.__c.__e = !0), e.__k && e.__k.some(fe));
}
function pe(e, t, n) {
	for (var r = 0; r < n.length; r++) ge(n[r], n[++r], n[++r]);
	u.__c && u.__c(t, e), e.some(function(t) {
		try {
			e = t.__h, t.__h = [], e.some(function(e) {
				e.call(t);
			});
		} catch (e) {
			u.__e(e, t.__v);
		}
	});
}
function me(e) {
	return typeof e != "object" || !e || e.__b > 0 ? e : D(e) ? e.map(me) : e.constructor === void 0 ? O({}, e) : null;
}
function he(e, t, n, r, i, a, o, s, c) {
	var d, f, p, m, h, g, _, v = n.props || w, y = t.props, b = t.type;
	if (b == "svg" ? i = "http://www.w3.org/2000/svg" : b == "math" ? i = "http://www.w3.org/1998/Math/MathML" : i ||= "http://www.w3.org/1999/xhtml", a != null) {
		for (d = 0; d < a.length; d++) if ((h = a[d]) && "setAttribute" in h == !!b && (b ? h.localName == b : h.nodeType == 3)) {
			e = h, a[d] = null;
			break;
		}
	}
	if (e == null) {
		if (b == null) return document.createTextNode(y);
		e = document.createElementNS(i, b, y.is && y), s &&= (u.__m && u.__m(t, a), !1), a = null;
	}
	if (b == null) v === y || s && e.data == y || (e.data = y);
	else {
		if (a = b == "textarea" && y.defaultValue != null ? null : a && l.call(e.childNodes), !s && a != null) for (v = {}, d = 0; d < e.attributes.length; d++) v[(h = e.attributes[d]).name] = h.value;
		for (d in v) h = v[d], d == "dangerouslySetInnerHTML" ? p = h : d == "children" || d in y || d == "value" && "defaultValue" in y || d == "checked" && "defaultChecked" in y || le(e, d, null, h, i);
		for (d in y) h = y[d], d == "children" ? m = h : d == "dangerouslySetInnerHTML" ? f = h : d == "value" ? g = h : d == "checked" ? _ = h : s && typeof h != "function" || v[d] === h || le(e, d, h, v[d], i);
		if (f) s || p && (f.__html == p.__html || f.__html == e.innerHTML) || (e.innerHTML = f.__html), t.__k = [];
		else if (p && (e.innerHTML = ""), ie(t.type == "template" ? e.content : e, D(m) ? m : [m], t, n, r, b == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, a, o, a ? a[0] : n.__k && P(n, 0), s, c), a != null) for (d = a.length; d--;) k(a[d]);
		s && b != "textarea" || (d = "value", b == "progress" && g == null ? e.removeAttribute("value") : g != null && (g !== e[d] || b == "progress" && !g || b == "option" && g != v[d]) && le(e, d, g, v[d], i), d = "checked", _ != null && _ != e[d] && le(e, d, _, v[d], i));
	}
	return e;
}
function ge(e, t, n) {
	try {
		if (typeof e == "function") {
			var r = typeof e.__u == "function";
			r && e.__u(), r && t == null || (e.__u = e(t));
		} else e.current = t;
	} catch (e) {
		u.__e(e, n);
	}
}
function _e(e, t, n) {
	var r, i;
	if (u.unmount && u.unmount(e), (r = e.ref) && (r.current && r.current != e.__e || ge(r, null, t)), (r = e.__c) != null) {
		if (r.componentWillUnmount) try {
			r.componentWillUnmount();
		} catch (e) {
			u.__e(e, t);
		}
		r.base = r.__P = r.__n = null;
	}
	if (r = e.__k) for (i = 0; i < r.length; i++) r[i] && _e(r[i], t, n || typeof e.type != "function");
	n || k(e.__e), e.__c = e.__ = e.__e = void 0;
}
function ve(e, t, n) {
	return this.constructor(e, n);
}
function ye(e, t, n) {
	var r, i, a, o;
	t == document && (t = document.documentElement), u.__ && u.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, a = [], o = [], de(t, e = (!r && n || t).__k = A(M, null, [e]), i || w, w, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? l.call(t.childNodes) : null, a, !r && n ? n : i ? i.__e : t.firstChild, r, o), pe(a, e, o), e.props.children = null;
}
l = T.slice, u = { __e: function(e, t, n, r) {
	for (var i, a, o; t = t.__;) if ((i = t.__c) && !i.__) try {
		if ((a = i.constructor) && a.getDerivedStateFromError != null && (i.setState(a.getDerivedStateFromError(e)), o = i.__d), i.componentDidCatch != null && (i.componentDidCatch(e, r || {}), o = i.__d), o) return i.__E = i;
	} catch (t) {
		e = t;
	}
	throw e;
} }, d = 0, f = function(e) {
	return e != null && e.constructor === void 0;
}, N.prototype.setState = function(e, t) {
	var n = this.__s != null && this.__s != this.state ? this.__s : this.__s = O({}, this.state);
	typeof e == "function" && (e = e(O({}, n), this.props)), e && O(n, e), e != null && this.__v && (t && this._sb.push(t), ne(this));
}, N.prototype.forceUpdate = function(e) {
	this.__v && (this.__e = !0, e && this.__h.push(e), ne(this));
}, N.prototype.render = M, p = [], h = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, g = function(e, t) {
	return e.__v.__b - t.__v.__b;
}, re.__r = 0, _ = Math.random().toString(8), v = "__d" + _, y = "__a" + _, b = /(PointerCapture)$|Capture$/i, x = 0, S = ue(!1), C = ue(!0);
//#endregion
//#region src/api.ts
var be = class extends Error {
	status;
	body;
	constructor(e, t, n = null) {
		super(e), this.name = "ApiError", this.status = t, this.body = n;
	}
}, xe = (e) => {
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
}, F = (e) => e instanceof Error ? e.message : String(e);
async function I(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new be(xe(r) || `请求失败（${n.status}）`, n.status);
	return r;
}
async function L(e, t, n = "POST", r) {
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
	if (!i.ok) throw new be(xe(a) || `请求失败（${i.status}）`, i.status, a);
	return a;
}
//#endregion
//#region node_modules/preact/hooks/dist/hooks.module.js
var R, z, Se, Ce, we = 0, Te = [], B = u, Ee = B.__b, De = B.__r, Oe = B.diffed, ke = B.__c, Ae = B.unmount, je = B.__;
function Me(e, t) {
	B.__h && B.__h(z, e, we || t), we = 0;
	var n = z.__H || (z.__H = {
		__: [],
		__h: []
	});
	return e >= n.__.length && n.__.push({}), n.__[e];
}
function V(e) {
	return we = 1, Ne(Ue, e);
}
function Ne(e, t, n) {
	var r = Me(R++, 2);
	if (r.t = e, !r.__c && (r.__ = [n ? n(t) : Ue(void 0, t), function(e) {
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
function Pe(e, t) {
	var n = Me(R++, 3);
	!B.__s && He(n.__H, t) && (n.__ = e, n.u = t, z.__H.__h.push(n));
}
function Fe(e, t) {
	var n = Me(R++, 4);
	!B.__s && He(n.__H, t) && (n.__ = e, n.u = t, z.__h.push(n));
}
function H(e) {
	return we = 5, Ie(function() {
		return { current: e };
	}, []);
}
function Ie(e, t) {
	var n = Me(R++, 7);
	return He(n.__H, t) && (n.__ = e(), n.__H = t, n.__h = e), n.__;
}
function Le() {
	for (var e; e = Te.shift();) {
		var t = e.__H;
		if (e.__P && t) try {
			t.__h.some(Be), t.__h.some(Ve), t.__h = [];
		} catch (n) {
			t.__h = [], B.__e(n, e.__v);
		}
	}
}
B.__b = function(e) {
	z = null, Ee && Ee(e);
}, B.__ = function(e, t) {
	e && t.__k && t.__k.__m && (e.__m = t.__k.__m), je && je(e, t);
}, B.__r = function(e) {
	De && De(e), R = 0;
	var t = (z = e.__c).__H;
	t && (Se === z ? (t.__h = [], z.__h = [], t.__.some(function(e) {
		e.__N && (e.__ = e.__N), e.u = e.__N = void 0;
	})) : (t.__h.some(Be), t.__h.some(Ve), t.__h = [], R = 0)), Se = z;
}, B.diffed = function(e) {
	Oe && Oe(e);
	var t = e.__c;
	t && t.__H && (t.__H.__h.length && (Te.push(t) !== 1 && Ce === B.requestAnimationFrame || ((Ce = B.requestAnimationFrame) || ze)(Le)), t.__H.__.some(function(e) {
		e.u &&= (e.__H = e.u, void 0);
	})), Se = z = null;
}, B.__c = function(e, t) {
	t.some(function(e) {
		try {
			e.__h.some(Be), e.__h = e.__h.filter(function(e) {
				return !e.__ || Ve(e);
			});
		} catch (n) {
			t.some(function(e) {
				e.__h &&= [];
			}), t = [], B.__e(n, e.__v);
		}
	}), ke && ke(e, t);
}, B.unmount = function(e) {
	Ae && Ae(e);
	var t, n = e.__c;
	n && n.__H && (n.__H.__.some(function(e) {
		try {
			Be(e);
		} catch (e) {
			t = e;
		}
	}), n.__H = void 0, t && B.__e(t, n.__v));
};
var Re = typeof requestAnimationFrame == "function";
function ze(e) {
	var t, n = function() {
		clearTimeout(r), Re && cancelAnimationFrame(t), setTimeout(e);
	}, r = setTimeout(n, 35);
	Re && (t = requestAnimationFrame(n));
}
function Be(e) {
	var t = z, n = e.__c;
	typeof n == "function" && (e.__c = void 0, n()), z = t;
}
function Ve(e) {
	var t = z;
	e.__c = e.__(), z = t;
}
function He(e, t) {
	return !e || e.length !== t.length || t.some(function(t, n) {
		return t !== e[n];
	});
}
function Ue(e, t) {
	return typeof t == "function" ? t(e) : t;
}
//#endregion
//#region node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var We = 0;
Array.isArray;
function U(e, t, n, r, i, a) {
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
		__v: --We,
		__i: -1,
		__u: 0,
		__source: i,
		__self: a
	};
	if (typeof e == "function" && (o = e.defaultProps)) for (s in o) c[s] === void 0 && (c[s] = o[s]);
	return u.vnode && u.vnode(l), l;
}
//#endregion
//#region src/islands/configuration.tsx
var Ge = "/api/configuration", Ke = "/api/pick-folder", qe = 8e3, Je = (e, t) => I(Ge, t), W = ({ html: e, class: t }) => /* @__PURE__ */ U("div", {
	class: t,
	dangerouslySetInnerHTML: { __html: e }
}), Ye = (e) => !(e instanceof be) || e.status !== 400 ? null : e.body?.errors ?? null;
function Xe({ facts: e }) {
	return /* @__PURE__ */ U("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configFactsTitle",
		children: /* @__PURE__ */ U("div", {
			class: "geist-fieldset-content",
			children: [/* @__PURE__ */ U(W, { html: t("configFactsTitle", "运行信息") }), /* @__PURE__ */ U("dl", {
				class: "configfacts",
				children: e.map((e) => /* @__PURE__ */ U(M, { children: [/* @__PURE__ */ U("dt", { children: e.term }), /* @__PURE__ */ U("dd", { children: e.value })] }))
			})]
		})
	});
}
function Ze({ data: e }) {
	let [n, r] = V(e.media_sources), [a, o] = V(""), s = H(null);
	Pe(() => () => s.current?.abort(), []);
	let c = async (e) => {
		if (s.current) return;
		let t = new AbortController();
		s.current = t, i(e, !0), o("");
		try {
			let e = await I(Ge, t.signal);
			t.signal.aborted || r(e.media_sources);
		} catch (e) {
			t.signal.aborted || o(F(e));
		} finally {
			s.current = null, i(e, !1);
		}
	};
	return n ? /* @__PURE__ */ U("section", {
		class: "configfieldset",
		"aria-labelledby": "configMountsTitle",
		children: /* @__PURE__ */ U("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ U(W, { html: t("configMountsTitle", "挂载状态") }),
				/* @__PURE__ */ U("dl", {
					class: "configfacts",
					children: n.map((e) => /* @__PURE__ */ U(M, { children: [/* @__PURE__ */ U("dt", { children: [
						e.location,
						" · ",
						e.root
					] }), /* @__PURE__ */ U("dd", { children: [
						e.path || "未配置挂载点",
						" · ",
						e.online ? "在线" : "离线"
					] })] }))
				}),
				a ? /* @__PURE__ */ U("p", {
					class: "configbad",
					role: "alert",
					children: a
				}) : null,
				/* @__PURE__ */ U("button", {
					type: "button",
					class: "geist-button",
					onClick: (e) => c(e.currentTarget),
					children: "刷新挂载状态"
				})
			]
		})
	}) : null;
}
function Qe({ data: e, receipt: r }) {
	let a = e.media_sources?.filter((e) => [
		"local",
		"115",
		"pikpak"
	].includes(e.location)), [o, s] = V(a?.length ? a.map((e) => e.path) : e.media_dirs.length ? e.media_dirs : [""]), [c, l] = V(a?.map((e) => e.location) ?? []), [u, d] = V(a?.map((e) => e.root) ?? []), [f, p] = V(String(e.port)), [m, h] = V(!1), [g, _] = V([]), [v, y] = V(""), [b, x] = V(""), [S, C] = V(null), [w, T] = V(null), E = H(!1), D = H(e.revision), O = H([]), k = H(null);
	Fe(() => {
		w !== null && (O.current[w]?.focus(), T(null));
	}, [w]), Pe(() => {
		if (!S) return;
		let e = setTimeout(() => location.assign(S.url), qe);
		return () => clearTimeout(e);
	}, [S]);
	let A = (e, t) => {
		s((n) => n.map((n, r) => r === e ? t : n));
	}, j = () => {
		T(o.length), s((e) => [...e, ""]);
	}, M = (e) => {
		l((t) => t.filter((t, n) => n !== e)), d((t) => t.filter((t, n) => n !== e)), s((t) => t.filter((t, n) => n !== e)), _((t) => t.filter((t, n) => n !== e));
	}, N = (e, t) => {
		_((n) => {
			let r = [...n];
			for (; r.length <= e;) r.push("");
			return r[e] = t, r;
		});
	}, P = async (e, t) => {
		if (t.getAttribute("aria-busy") !== "true") {
			i(t, !0);
			try {
				let { path: t } = await L(Ke, { initial: o[e] ?? "" });
				t && (A(e, t), N(e, ""));
			} catch (t) {
				N(e, F(t));
			} finally {
				i(t, !1);
			}
		}
	};
	return S ? /* @__PURE__ */ U("div", {
		class: "configsaved",
		role: "status",
		children: [/* @__PURE__ */ U(W, { html: n("配置已保存，Peach 正在重新启动。", {
			variant: "success",
			label: "已保存"
		}) }), /* @__PURE__ */ U("p", {
			class: "confighelp",
			children: [
				"几秒后自动打开新地址；没跳转就点 ",
				/* @__PURE__ */ U("a", {
					href: S.url,
					children: "进入馆藏"
				}),
				"。"
			]
		})]
	}) : /* @__PURE__ */ U("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configTitle",
		onSubmit: async (t) => {
			if (t.preventDefault(), !E.current) {
				E.current = !0, i(k.current, !0), x("");
				try {
					let t = await L(Ge, {
						revision: D.current,
						media_dirs: o,
						...e.media_sources ? { media_sources: o.map((e, t) => ({
							path: e,
							location: c[t] || "local",
							root: u[t] || ""
						})) } : {},
						port: f,
						scan_now: m
					});
					D.current = t.revision, _([]), y(""), r("已保存配置"), C(t);
				} catch (e) {
					let t = Ye(e);
					t ? (_(t.media_dirs ?? []), y(t.port ?? "")) : (_([]), y(""), x(F(e)));
				} finally {
					E.current = !1, i(k.current, !1);
				}
			}
		},
		noValidate: !0,
		children: [/* @__PURE__ */ U("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ U(W, { html: t("configTitle", "这台电脑") }),
				/* @__PURE__ */ U("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ U("span", {
							class: "configlabel",
							id: "configDirsLabel",
							children: "媒体文件夹"
						}),
						/* @__PURE__ */ U("div", {
							class: "configdirs",
							role: "group",
							"aria-labelledby": "configDirsLabel",
							children: o.map((t, n) => /* @__PURE__ */ U("div", {
								class: "configdir",
								children: [
									/* @__PURE__ */ U("input", {
										class: "geist-input",
										type: "text",
										value: t,
										"aria-label": `媒体文件夹 ${n + 1}`,
										"aria-invalid": g[n] ? "true" : void 0,
										onInput: (e) => A(n, e.currentTarget.value),
										ref: (e) => {
											O.current[n] = e;
										}
									}),
									/* @__PURE__ */ U("button", {
										type: "button",
										class: "geist-button configpick",
										"aria-label": "选择文件夹",
										onClick: (e) => P(n, e.currentTarget),
										children: /* @__PURE__ */ U("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ U("use", { href: "#i-folder-search" })
										})
									}),
									o.length > 1 ? /* @__PURE__ */ U("button", {
										type: "button",
										class: "geist-button configrm",
										"aria-label": "移除这个文件夹",
										onClick: () => M(n),
										children: /* @__PURE__ */ U("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ U("use", { href: "#i-x" })
										})
									}) : null,
									/* @__PURE__ */ U("div", {
										class: "configsource",
										children: [/* @__PURE__ */ U("label", { children: ["媒体来源", /* @__PURE__ */ U("select", {
											class: "geist-input",
											"aria-label": `媒体来源 ${n + 1}`,
											value: c[n] || "local",
											onChange: (e) => {
												let t = [...c];
												t[n] = e.currentTarget.value, l(t);
											},
											children: [
												/* @__PURE__ */ U("option", {
													value: "local",
													children: "本地磁盘"
												}),
												/* @__PURE__ */ U("option", {
													value: "115",
													children: "CloudDrive · 115"
												}),
												/* @__PURE__ */ U("option", {
													value: "pikpak",
													children: "CloudDrive · PikPak"
												})
											]
										})] }), e.windows === !1 ? /* @__PURE__ */ U("label", { children: ["账本根目录", /* @__PURE__ */ U("input", {
											class: "geist-input",
											"aria-label": `账本根目录 ${n + 1}`,
											value: u[n] || "",
											placeholder: "例如 B:\\\\",
											onInput: (e) => {
												let t = [...u];
												t[n] = e.currentTarget.value, d(t);
											}
										})] }) : null]
									}),
									g[n] ? /* @__PURE__ */ U("p", {
										class: "configbad",
										role: "alert",
										children: g[n]
									}) : null
								]
							}, n))
						}),
						/* @__PURE__ */ U("button", {
							type: "button",
							class: "geist-button configadd",
							onClick: j,
							children: "添加文件夹"
						}),
						/* @__PURE__ */ U("p", {
							class: "confighelp",
							children: ["CloudDrive：先登录网盘并挂载，再选择对应的 115 或 PikPak 来源。macOS 填本机挂载点与对应的账本盘符根。", /* @__PURE__ */ U("a", {
								href: "https://www.clouddrive2.com/help.html",
								target: "_blank",
								rel: "noreferrer",
								children: "挂载帮助"
							})]
						})
					]
				}),
				/* @__PURE__ */ U("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ U("label", {
							for: "configPort",
							children: "本机访问端口"
						}),
						/* @__PURE__ */ U("input", {
							id: "configPort",
							class: "geist-input",
							type: "text",
							inputMode: "numeric",
							value: f,
							"aria-invalid": v ? "true" : void 0,
							onInput: (e) => p(e.currentTarget.value)
						}),
						v ? /* @__PURE__ */ U("p", {
							class: "configbad",
							role: "alert",
							children: v
						}) : null,
						/* @__PURE__ */ U("p", {
							class: "confighelp",
							children: "浏览器地址里冒号后面的数字，一般不用改。"
						})
					]
				}),
				/* @__PURE__ */ U("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ U("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ U("input", {
							type: "checkbox",
							checked: m,
							onChange: (e) => h(e.currentTarget.checked)
						}), /* @__PURE__ */ U("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ U("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ U("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ U("span", { children: "保存后扫描媒体文件夹" })]
				}),
				b ? /* @__PURE__ */ U(W, { html: n(b, {
					variant: "error",
					label: "没有保存"
				}) }) : null
			]
		}), /* @__PURE__ */ U("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [/* @__PURE__ */ U("p", { children: "保存后 Peach 会重新启动，端口改了就用新地址打开。" }), /* @__PURE__ */ U("button", {
				type: "submit",
				class: "geist-button primary",
				ref: k,
				children: "保存配置"
			})]
		})]
	});
}
function $e({ receipt: e, data: t, error: r }) {
	return r || !t ? /* @__PURE__ */ U(W, {
		class: "configpage",
		html: n(r || "没有读到配置", {
			variant: "error",
			label: "打不开配置"
		})
	}) : /* @__PURE__ */ U("div", {
		class: "configpage",
		children: [
			t.editable ? /* @__PURE__ */ U(Qe, {
				data: t,
				receipt: e
			}) : /* @__PURE__ */ U(W, { html: n(t.notice, {
				variant: "secondary",
				label: "只读"
			}) }),
			/* @__PURE__ */ U(Xe, { facts: t.facts }),
			/* @__PURE__ */ U(Ze, { data: t })
		]
	});
}
//#endregion
//#region node_modules/@preact/signals-core/dist/signals-core.module.js
var et = Symbol.for("preact-signals");
function tt() {
	if (J > 1) J--;
	else {
		var e, t = !1;
		for ((function() {
			var e = st;
			for (st = void 0; e !== void 0;) {
				var t = e.S;
				if (t.v === e.v) for (var n = t.t; n !== void 0; n = n.x) n.i === e.i && (n.i = t.i);
				e = e.o;
			}
		})(); q !== void 0;) {
			var n = q;
			for (q = void 0, it++; n !== void 0;) {
				var r = n.u;
				if (n.u = void 0, n.f &= -3, !(8 & n.f) && dt(n)) try {
					n.c();
				} catch (n) {
					t ||= (e = n, !0);
				}
				n = r;
			}
		}
		if (it = 0, J--, t) throw e;
	}
}
function nt(e) {
	if (J > 0) return e();
	ot = ++at, J++;
	try {
		return e();
	} finally {
		tt();
	}
}
var G, K = void 0;
function rt(e) {
	var t = K, n = G;
	K = void 0, G = void 0;
	try {
		return e();
	} finally {
		K = t, G = n;
	}
}
var q = void 0, J = 0, it = 0, at = 0, ot = 0, st = void 0, ct = 0;
function lt(e) {
	if (K !== void 0) {
		var t = e.n;
		if (t === void 0 || t.t !== K) return t = {
			i: 0,
			S: e,
			p: K.s,
			n: void 0,
			t: K,
			e: void 0,
			x: void 0,
			r: t
		}, K.s !== void 0 && (K.s.n = t), K.s = t, e.n = t, 32 & K.f && e.S(t), t;
		if (t.i === -1) return t.i = 0, t.n !== void 0 && (t.n.p = t.p, t.p !== void 0 && (t.p.n = t.n), t.p = K.s, t.n = void 0, K.s.n = t, K.s = t), t;
	}
}
function Y(e, t) {
	this.v = e, this.i = 0, this.n = void 0, this.t = void 0, this.l = 0, this.W = t?.watched, this.Z = t?.unwatched, this.name = t?.name;
}
Y.prototype.brand = et, Y.prototype.h = function() {
	return !0;
}, Y.prototype.S = function(e) {
	var t = this, n = this.t;
	n !== e && e.e === void 0 && (e.x = n, this.t = e, n === void 0 ? rt(function() {
		var e;
		(e = t.W) == null || e.call(t);
	}) : n.e = e);
}, Y.prototype.U = function(e) {
	var t = this;
	if (this.t !== void 0) {
		var n = e.e, r = e.x;
		n !== void 0 && (n.x = r, e.e = void 0), r !== void 0 && (r.e = n, e.x = void 0), e === this.t && (this.t = r, r === void 0 && rt(function() {
			var e;
			(e = t.Z) == null || e.call(t);
		}));
	}
}, Y.prototype.subscribe = function(e) {
	var t = this;
	return Q(function() {
		var n = t.value;
		rt(function() {
			return e(n);
		});
	}, { name: "sub" });
}, Y.prototype.valueOf = function() {
	return this.value;
}, Y.prototype.toString = function() {
	return this.value + "";
}, Y.prototype.toJSON = function() {
	return this.value;
}, Y.prototype.peek = function() {
	var e = this;
	return rt(function() {
		return e.value;
	});
}, Object.defineProperty(Y.prototype, "value", {
	get: function() {
		var e = lt(this);
		return e !== void 0 && (e.i = this.i), this.v;
	},
	set: function(e) {
		if (e !== this.v) {
			if (it > 100) throw Error("Cycle detected");
			(function(e) {
				J !== 0 && it === 0 && e.l !== ot && (e.l = ot, st = {
					S: e,
					v: e.v,
					i: e.i,
					o: st
				});
			})(this), this.v = e, this.i++, ct++, J++;
			try {
				for (var t = this.t; t !== void 0; t = t.x) t.t.N();
			} finally {
				tt();
			}
		}
	}
});
function ut(e, t) {
	return new Y(e, t);
}
function dt(e) {
	for (var t = e.s; t !== void 0; t = t.n) if (t.S.i !== t.i || !t.S.h() || t.S.i !== t.i) return !0;
	return !1;
}
function ft(e) {
	for (var t = e.s; t !== void 0; t = t.n) {
		var n = t.S.n;
		if (n !== void 0 && (t.r = n), t.S.n = t, t.i = -1, t.n === void 0) {
			e.s = t;
			break;
		}
	}
}
function pt(e) {
	for (var t = e.s, n = void 0; t !== void 0;) {
		var r = t.p;
		t.i === -1 ? (t.S.U(t), r !== void 0 && (r.n = t.n), t.n !== void 0 && (t.n.p = r)) : n = t, t.S.n = t.r, t.r !== void 0 && (t.r = void 0), t = r;
	}
	e.s = n;
}
function X(e, t) {
	Y.call(this, void 0, t), this.x = e, this.s = void 0, this.g = ct - 1, this.f = 4;
}
X.prototype = new Y(), X.prototype.h = function() {
	if (this.f &= -3, 1 & this.f) return !1;
	if ((36 & this.f) == 32 || (this.f &= -5, this.g === ct)) return !0;
	if (this.g = ct, this.f |= 1, this.i > 0 && !dt(this)) return this.f &= -2, !0;
	var e = K;
	try {
		ft(this), K = this;
		var t = this.x();
		(16 & this.f || this.v !== t || this.i === 0) && (this.v = t, this.f &= -17, this.i++);
	} catch (e) {
		this.v = e, this.f |= 16, this.i++;
	}
	return K = e, pt(this), this.f &= -2, !0;
}, X.prototype.S = function(e) {
	if (this.t === void 0) {
		this.f |= 36;
		for (var t = this.s; t !== void 0; t = t.n) t.S.S(t);
	}
	Y.prototype.S.call(this, e);
}, X.prototype.U = function(e) {
	if (this.t !== void 0 && (Y.prototype.U.call(this, e), this.t === void 0)) {
		this.f &= -33;
		for (var t = this.s; t !== void 0; t = t.n) t.S.U(t);
	}
}, X.prototype.N = function() {
	if (!(2 & this.f)) {
		this.f |= 6;
		for (var e = this.t; e !== void 0; e = e.x) e.t.N();
	}
}, Object.defineProperty(X.prototype, "value", { get: function() {
	if (1 & this.f) throw Error("Cycle detected");
	var e = lt(this);
	if (this.h(), e !== void 0 && (e.i = this.i), 16 & this.f) throw this.v;
	return this.v;
} });
function mt(e, t) {
	return new X(e, t);
}
function ht(e) {
	var t = e.m;
	if (e.m = void 0, typeof t == "function") {
		J++;
		var n = K;
		K = void 0;
		try {
			t();
		} catch (t) {
			throw e.f &= -2, e.f |= 8, gt(e), t;
		} finally {
			K = n, tt();
		}
	}
}
function gt(e) {
	for (var t = e.s; t !== void 0; t = t.n) t.S.U(t);
	e.x = void 0, e.s = void 0, ht(e);
}
function _t(e) {
	if (K !== this) throw Error("Out-of-order effect");
	pt(this), K = e, this.f &= -2, 8 & this.f && gt(this), tt();
}
function Z(e, t) {
	this.x = e, this.m = void 0, this.s = void 0, this.u = void 0, this.f = 32, this.name = t?.name, G && G.push(this);
}
Z.prototype.c = function() {
	var e = this.S();
	try {
		if (8 & this.f || this.x === void 0) return;
		var t = this.x();
		typeof t == "function" && (this.m = t);
	} finally {
		e();
	}
}, Z.prototype.S = function() {
	if (1 & this.f) throw Error("Cycle detected");
	this.f |= 1, this.f &= -9, ht(this), ft(this), J++;
	var e = K;
	return K = this, _t.bind(this, e);
}, Z.prototype.N = function() {
	2 & this.f || (this.f |= 2, this.u = q, q = this);
}, Z.prototype.d = function() {
	this.f |= 8, 1 & this.f || gt(this);
}, Z.prototype.dispose = function() {
	this.d();
};
function Q(e, t) {
	var n = new Z(e, t);
	try {
		n.c();
	} catch (e) {
		throw n.d(), e;
	}
	var r = n.d.bind(n);
	return r[Symbol.dispose] = r, r;
}
//#endregion
//#region node_modules/@preact/signals/dist/signals.module.js
var vt, yt, bt = typeof window < "u" && !!window.__PREACT_SIGNALS_DEVTOOLS__, xt = [];
Q(function() {
	vt = this.N;
})();
function $(e, t) {
	u[e] = t.bind(null, u[e] || function() {});
}
function St(e) {
	if (yt) {
		var t = yt;
		yt = void 0, t();
	}
	yt = e && e.S();
}
function Ct(e) {
	var t = this, n = e.data, r = Tt(n);
	r.name = "ReactiveDom", r.value = n;
	var i = Ie(function() {
		for (var e = t, n = t.__v; n = n.__;) if (n.__c) {
			n.__c.__$f |= 4;
			break;
		}
		var i = mt(function() {
			var e = r.value.value;
			return e === 0 ? 0 : !0 === e ? "" : e || "";
		}), a = mt(function() {
			return !Array.isArray(i.value) && !f(i.value);
		}), o = Q(function() {
			if (this.N = Ot, a.value) {
				var t = i.value;
				e.__v && e.__v.__e && e.__v.__e.nodeType === 3 && (e.__v.__e.data = t);
			}
		}), s = t.__$u.d;
		return t.__$u.d = function() {
			o(), s.call(this);
		}, [a, i];
	}, []), a = i[0], o = i[1];
	return a.value ? o.peek() : o.value;
}
Ct.displayName = "ReactiveTextNode", Object.defineProperties(Y.prototype, {
	constructor: {
		configurable: !0,
		value: void 0
	},
	type: {
		configurable: !0,
		value: Ct
	},
	props: {
		configurable: !0,
		get: function() {
			var e = this;
			return { data: { get value() {
				return e.value;
			} } };
		}
	},
	__b: {
		configurable: !0,
		value: 1
	}
}), $("__b", function(e, t) {
	if (typeof t.type == "string") {
		var n, r = t.props;
		for (var i in r) if (i !== "children") {
			var a = r[i];
			a instanceof Y && (n || (t.__np = n = {}), n[i] = a, r[i] = a.peek());
		}
	}
	e(t);
}), $("__r", function(e, t) {
	if (e(t), t.type !== M) {
		St();
		var n, r = t.__c;
		r && (r.__$f &= -2, (n = r.__$u) === void 0 && (r.__$u = n = function(e, t) {
			var n;
			return Q(function() {
				n = this;
			}, { name: t }), n.c = e, n;
		}(function(e) {
			return function() {
				var t;
				bt && ((t = this.y) == null || t.call(this)), e.__$f |= 1, e.setState({});
			};
		}(r), typeof t.type == "function" ? t.type.displayName || t.type.name : ""))), St(n);
	}
}), $("__e", function(e, t, n, r) {
	St(), e(t, n, r);
}), $("diffed", function(e, t) {
	St();
	var n;
	if (typeof t.type == "string" && (n = t.__e)) {
		var r = t.__np, i = t.props, a = n.U;
		if (a) for (var o in a) {
			var s = a[o];
			s === void 0 || r && o in r || (s.d(), a[o] = void 0);
		}
		if (r) for (var c in a || (a = {}, n.U = a), r) {
			var l = a[c], u = r[c];
			l === void 0 ? (l = wt(n, c, u, i), a[c] = l) : l.o(u, i);
		}
	}
	e(t);
});
function wt(e, t, n, r) {
	var i = t in e && e.ownerSVGElement === void 0, a = ut(n);
	return {
		o: function(e, t) {
			a.value = e, r = t;
		},
		d: Q(function() {
			this.N = Ot;
			var n = a.value.value;
			r[t] !== n && (r[t] = n, i ? e[t] = n : n != null && (!1 !== n || t[4] === "-") ? e.setAttribute(t, n) : e.removeAttribute(t));
		})
	};
}
$("unmount", function(e, t) {
	if (typeof t.type == "string") {
		var n = t.__e;
		if (n) {
			var r = n.U;
			if (r) for (var i in n.U = void 0, r) {
				var a = r[i];
				a && a.d();
			}
		}
		var o = t.__np;
		if (o) {
			var s = t.props;
			for (var c in o) s[c] = o[c];
		}
		t.__np = void 0;
	} else {
		var l = t.__c;
		if (l) {
			var u = l.__$u;
			u && (l.__$u = void 0, u.d());
		}
	}
	e(t);
}), $("__h", function(e, t, n, r) {
	r < 3 && (t.__$f |= 2), e(t, n, r);
}), N.prototype.shouldComponentUpdate = function(e, t) {
	if (this.__R) return !0;
	var n = this.__$u, r = n && n.s !== void 0;
	for (var i in t) return !0;
	if (this.__f || typeof this.u == "boolean" && !0 === this.u) {
		var a = 2 & this.__$f;
		if (!(r || a || 4 & this.__$f) || 1 & this.__$f) return !0;
	} else if (!(r || 4 & this.__$f) || 3 & this.__$f) return !0;
	for (var o in e) if (o !== "__source" && e[o] !== this.props[o]) return !0;
	for (var s in this.props) if (!(s in e)) return !0;
	return !1;
};
function Tt(e, t) {
	return Ie(function() {
		return ut(e, t);
	}, []);
}
var Et = function(e) {
	queueMicrotask(function() {
		queueMicrotask(e);
	});
};
function Dt() {
	nt(function() {
		for (var e; e = xt.shift();) vt.call(e);
	});
}
function Ot() {
	xt.push(this) === 1 && (u.requestAnimationFrame || Et)(Dt);
}
//#endregion
//#region src/state/quality-goals.ts
var kt = "/api/quality-goals?limit=200", At = {
	data: null,
	error: ""
}, jt = ut(At), Mt = 0, Nt = mt(() => jt.value);
mt(() => jt.value.data?.total ?? null);
function Pt() {
	Mt += 1, jt.value = At;
}
async function Ft(e) {
	let t = Mt += 1;
	try {
		let n = await I(kt, e);
		return t === Mt && (jt.value = {
			data: n,
			error: ""
		}), n;
	} catch (n) {
		throw !e?.aborted && t === Mt && (jt.value = {
			data: null,
			error: F(n)
		}), n;
	}
}
//#endregion
//#region src/islands/quality-goals.tsx
var It = (e, t) => Ft(t), Lt = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
function Rt({ openItem: t, javTitleHtml: r, javDisplayName: i, srcBadge: a }) {
	let { data: l, error: u } = Nt.value;
	if (u) return /* @__PURE__ */ U("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: n(u, {
			variant: "error",
			label: "读取失败"
		}) }
	});
	let d = l?.items ?? [];
	return d.length ? /* @__PURE__ */ U("div", {
		class: "qualitylist",
		children: d.map((e) => /* @__PURE__ */ U("article", {
			class: "qualityitem",
			children: [/* @__PURE__ */ U("button", {
				class: "qualitycover",
				type: "button",
				"aria-label": `打开 ${i(e)}`,
				onClick: () => t(e.id),
				children: /* @__PURE__ */ U("img", {
					src: Lt(e),
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove()
				})
			}), /* @__PURE__ */ U("div", { children: [
				/* @__PURE__ */ U("h3", { children: /* @__PURE__ */ U("button", {
					type: "button",
					"data-middle-truncate": !0,
					onClick: () => t(e.id),
					dangerouslySetInnerHTML: { __html: r(e) }
				}) }),
				/* @__PURE__ */ U("p", {
					class: "mono",
					children: [
						/* @__PURE__ */ U("span", {
							style: "display:contents",
							dangerouslySetInnerHTML: { __html: a(e.location, e.cost) }
						}),
						/* @__PURE__ */ U("span", { children: o[e.location] ?? e.location }),
						/* @__PURE__ */ U("span", { children: s(e.duration) }),
						/* @__PURE__ */ U("span", { children: c(e.size ?? 0) })
					]
				}),
				e.reason ? /* @__PURE__ */ U("p", { children: e.reason }) : null
			] })]
		}, e.id))
	}) : /* @__PURE__ */ U("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: e("sparkles", "没有标记中的高清版目标", "现有版本都已满足条件，或还没有加入追踪。") }
	});
}
//#endregion
//#region src/jobs.ts
async function zt(e) {
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
function Bt(e) {
	let t = document.createElement("div");
	e.host.hidden = !0, t.dataset.followJob = "", t.setAttribute("aria-live", "polite"), e.host.prepend(t);
	let n = e.storageKey || "peach-follow-job", r = sessionStorage.getItem(n) || void 0, i = !1;
	zt({
		read: e.read,
		active: () => !i && e.active() && t.isConnected,
		keepWatching: e.watchIdle !== !1,
		render: (a) => {
			let o = a.status === "running";
			if (e.host.hidden = !o, e.busy(o), o) {
				r = a.job_id, r && sessionStorage.setItem(n, r);
				let i = a.current, o = (i?.attempt || 1) > 1 ? ` · 第 ${i?.attempt}/${i?.max_attempts} 次尝试${i?.retry_in ? `，${i.retry_in} 秒后重试` : ""}` : "", s = (e.title || (a.total ? `${a.older ? "抓取历史" : "检查更新"}：已完成 ${a.checked || 0}/${a.total} 个来源` : "正在准备检查任务…")) + (i ? ` · ${i.label || i.provider || ""}${o}` : ""), c = e.loading(s) + ((a.total || 0) > 0 ? e.progress(a.checked || 0, a.total) : "");
				t.innerHTML = e.container ? e.container(c) : c;
			} else if (r && r === a.job_id) r = void 0, i = !0, e.host.hidden = a.status !== "failed", sessionStorage.removeItem(n), t.innerHTML = a.status === "failed" ? e.note(a.error || "检查失败") : "", e.complete(a);
			else {
				if (r && a.status === "idle") {
					e.host.hidden = !1, t.innerHTML = e.note("任务状态已失效，请重新发起任务"), sessionStorage.removeItem(n), i = !0;
					return;
				}
				t.innerHTML = "";
			}
		},
		disconnected: () => {
			e.host.hidden = !1, t.innerHTML = e.note("暂时无法读取进度，正在重新连接…");
		}
	});
}
//#endregion
//#region src/islands/scraping.tsx
var Vt = (e, t) => I("/api/scraping", t);
function Ht({ value: e, onChange: t }) {
	let n = H(null), i = H(t);
	return i.current = t, Fe(() => {
		let t = n.current;
		t.innerHTML = r([
			["environment", "系统代理"],
			["direct", "应用直连"],
			["proxy", "自定义代理"]
		], e, { label: "连接方式" });
		let o = a(t.firstElementChild), s = () => i.current(o.value);
		return o.addEventListener("change", s), () => {
			o.disabled = !0, o.removeEventListener("change", s), t.replaceChildren();
		};
	}, []), /* @__PURE__ */ U("div", {
		ref: n,
		class: "scraping-network"
	});
}
function Ut({ source: e, toast: r }) {
	let [a, o] = V(e), [s, c] = V(e.network), [l, u] = V(""), [d, f] = V(""), [p, m] = V(""), [h, g] = V("paste"), [_, v] = V(""), [y, b] = V(!1), [x, S] = V(""), [C, w] = V([]), T = H(null), E = H(null);
	Fe(() => {
		E.current?.querySelectorAll("footer button").forEach((e) => i(e, y));
	}, [y]);
	let D = H(new AbortController());
	Pe(() => () => D.current.abort(), []);
	async function O(t) {
		if (!y) {
			b(!0), S(""), w([]);
			try {
				if (t === "check") {
					let t = await L("/api/scraping/check", { source: e.source }, "POST", D.current.signal);
					D.current.signal.aborted || w(t.results);
				} else {
					let n = await L("/api/scraping/settings", {
						source: e.source,
						network: s,
						proxy: l,
						cookie: d,
						cookies_text: p,
						revoke: t === "revoke"
					}, "POST", D.current.signal);
					D.current.signal.aborted || (o(n.saved), u(""), f(""), m(""), v(""), T.current && (T.current.value = ""), r(t === "revoke" ? "Cookie 已撤销" : "来源设置已保存"));
				}
			} catch (e) {
				D.current.signal.aborted || S(F(e));
			} finally {
				D.current.signal.aborted || b(!1);
			}
		}
	}
	return /* @__PURE__ */ U("section", {
		class: "scraping-source",
		children: /* @__PURE__ */ U("form", {
			ref: E,
			class: "cleanupfieldset",
			"data-geist-fieldset": !0,
			onSubmit: (e) => {
				e.preventDefault(), O("save");
			},
			children: [/* @__PURE__ */ U("div", {
				class: "geist-fieldset-content scraping-fields",
				children: [
					/* @__PURE__ */ U("div", { dangerouslySetInnerHTML: { __html: t(`scraping-${e.source}`, e.label) } }),
					/* @__PURE__ */ U("a", {
						class: "scraping-url",
						href: e.login,
						target: "_blank",
						rel: "noopener noreferrer",
						children: e.login
					}),
					/* @__PURE__ */ U("div", {
						class: "scraping-label",
						children: ["连接方式", /* @__PURE__ */ U(Ht, {
							value: s,
							onChange: c
						})]
					}),
					s === "proxy" && /* @__PURE__ */ U("label", { children: ["代理地址", /* @__PURE__ */ U("input", {
						class: "geist-input",
						type: "password",
						autoComplete: "off",
						value: l,
						placeholder: a.proxy_saved ? "已保存，留空保留" : "http://127.0.0.1:7890",
						disabled: y,
						onInput: (e) => u(e.currentTarget.value)
					})] }),
					e.accepts_cookie && /* @__PURE__ */ U(M, { children: [
						/* @__PURE__ */ U("p", { children: a.cookie_saved ? "Cookie 已保存，登录是否有效请在抓取时确认。" : "需要登录时，任选一种方式提供 Cookie。" }),
						/* @__PURE__ */ U("div", {
							class: "insightswitch scraping-cookie-method",
							role: "radiogroup",
							"aria-label": "提供 Cookie 的方式（二选一）",
							children: [["paste", "粘贴 Cookie"], ["file", "导入文件"]].map(([t, n]) => /* @__PURE__ */ U("label", { children: [/* @__PURE__ */ U("input", {
								type: "radio",
								name: `cookie-method-${e.source}`,
								value: t,
								checked: h === t,
								onChange: () => {
									g(t), f(""), m(""), v("");
								}
							}), /* @__PURE__ */ U("span", { children: n })] }, t))
						}),
						h === "paste" ? /* @__PURE__ */ U("label", { children: ["Cookie", /* @__PURE__ */ U("input", {
							class: "geist-input",
							type: "password",
							autoComplete: "off",
							value: d,
							disabled: y,
							onInput: (e) => f(e.currentTarget.value)
						})] }) : /* @__PURE__ */ U("label", {
							class: "scraping-file",
							children: ["Netscape Cookie 文件（.txt）", /* @__PURE__ */ U("span", {
								class: "scraping-file-control",
								children: [
									/* @__PURE__ */ U("span", {
										class: "geist-button",
										children: "选择文件"
									}),
									/* @__PURE__ */ U("span", {
										class: "scraping-file-name",
										children: _ || "未选择文件"
									}),
									/* @__PURE__ */ U("input", {
										ref: T,
										type: "file",
										accept: ".txt",
										disabled: y,
										onChange: async (e) => {
											let t = e.currentTarget.files?.[0];
											if (!t) {
												m(""), v("");
												return;
											}
											if (m(""), t.size > 262144) {
												S("Cookie 文本超过 256 KiB"), e.currentTarget.value = "";
												return;
											}
											b(!0);
											try {
												let e = await t.text();
												D.current.signal.aborted || (m(e), v(t.name));
											} catch {
												D.current.signal.aborted || S("Cookie 文件未读取，请重新选择");
											} finally {
												D.current.signal.aborted || b(!1);
											}
										}
									})
								]
							})]
						})
					] }),
					x && /* @__PURE__ */ U("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: n(x, { variant: "error" }) }
					}),
					C.map((t) => /* @__PURE__ */ U("div", {
						role: "status",
						dangerouslySetInnerHTML: { __html: n(`${e.label}${t.label === "来源页面" ? "" : " 高清图片"}：${t.ok ? "可连接" : "不能连接"}` + (t.width ? ` · ${t.width} × ${t.height}` : "") + (t.message ? `。${t.message}` : ""), { variant: t.ok ? "success" : "error" }) }
					}, t.label))
				]
			}), /* @__PURE__ */ U("footer", {
				class: "geist-fieldset-footer",
				"data-geist-fieldset-footer": !0,
				children: [
					/* @__PURE__ */ U("button", {
						class: "geist-button primary",
						type: "submit",
						children: "保存"
					}),
					/* @__PURE__ */ U("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void O("check"),
						children: "检查连接"
					}),
					e.accepts_cookie && a.cookie_saved && /* @__PURE__ */ U("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void O("revoke"),
						children: "撤销 Cookie"
					})
				]
			})]
		})
	});
}
function Wt({ data: e, error: r, toast: a }) {
	let [o, s] = V(""), [c, l] = V(!1), [u, d] = V(""), f = H(null);
	Fe(() => i(f.current, c), [c]);
	let p = H(new AbortController()), m = H(0);
	async function h(e = !1) {
		let t = ++m.current;
		await zt({
			read: (e) => I("/api/scraping/cover", e),
			active: () => !p.current.signal.aborted && t === m.current,
			render: (t) => {
				l(t.status === "running"), t.status === "running" && (e = !1), t.status === "failed" && !e && d(t.error || "采集未取得"), t.status === "complete" && !e && a(t.result || "封面采集完成");
			},
			disconnected: () => d("连接中断，正在重新读取后台进度")
		});
	}
	Pe(() => (h(!0), () => p.current.abort()), []);
	async function g() {
		if (!c) {
			m.current++, l(!0), d("");
			try {
				await L("/api/scraping/cover", { code: o }, "POST", p.current.signal), await h();
			} catch (e) {
				p.current.signal.aborted || (l(!1), d(F(e)));
			}
		}
	}
	return r ? /* @__PURE__ */ U("div", {
		role: "alert",
		dangerouslySetInnerHTML: { __html: n(r, { variant: "error" }) }
	}) : /* @__PURE__ */ U("div", {
		class: "scraping-page",
		children: [
			/* @__PURE__ */ U("p", { children: "高清图片可能需要代理才能下载，请先检查连接。" }),
			/* @__PURE__ */ U("section", {
				class: "cleanupfieldset scraping-source",
				"data-geist-fieldset": !0,
				children: /* @__PURE__ */ U("div", {
					class: "geist-fieldset-content scraping-fields",
					children: [
						/* @__PURE__ */ U("div", { dangerouslySetInnerHTML: { __html: t("scraping-cover", "高清封面") } }),
						/* @__PURE__ */ U("form", {
							class: "scraping-cover-form",
							onSubmit: (e) => {
								e.preventDefault(), g();
							},
							children: [/* @__PURE__ */ U("input", {
								class: "geist-input",
								"aria-label": "馆藏番号",
								required: !0,
								value: o,
								disabled: c,
								placeholder: "输入馆藏番号，如 ABW-232",
								onInput: (e) => s(e.currentTarget.value)
							}), /* @__PURE__ */ U("button", {
								ref: f,
								class: "geist-button primary",
								type: "submit",
								children: "抓取封面"
							})]
						}),
						u && /* @__PURE__ */ U("div", {
							role: "alert",
							dangerouslySetInnerHTML: { __html: n(u, { variant: "error" }) }
						})
					]
				})
			}),
			e?.sources.map((e) => /* @__PURE__ */ U(Ut, {
				source: e,
				toast: a
			}, e.source))
		]
	});
}
//#endregion
//#region src/state/index.ts
var Gt = { "quality-goals": {
	refresh: Ft,
	reset: Pt
} }, Kt = () => Object.keys(Gt);
async function qt(e) {
	let t = Gt[e];
	if (!t) throw Error(`未登记的共享 store：${String(e)}`);
	try {
		return await t.refresh(), !0;
	} catch {
		return !1;
	}
}
//#endregion
//#region src/sidebar.ts
function Jt(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function Yt(e, t) {
	return e.dataset.surface === t && e.querySelector(".dnav") ? !1 : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function Xt(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/islands.ts
var Zt = {
	scraping: {
		load: Vt,
		component: Wt
	},
	"quality-goals": {
		load: It,
		component: Rt
	},
	configuration: {
		load: Je,
		component: $e
	}
}, Qt = () => Object.keys(Zt), $t = /* @__PURE__ */ new Map();
async function en(e, t, n, r = {}) {
	let i = Zt[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	tn(t);
	let a = {
		controller: new AbortController(),
		painted: !1
	};
	$t.set(t, a);
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
			error: F(e)
		};
	}
	if ($t.get(t) !== a) return;
	if (r.isCurrent && !r.isCurrent()) {
		$t.delete(t);
		return;
	}
	t.textContent = "", a.painted = !0;
	let s = {
		...n,
		...o
	};
	ye(A(i.component, s), t);
}
function tn(e) {
	let t = $t.get(e);
	t && (t.controller.abort(), $t.delete(e), t.painted && ye(null, e));
}
//#endregion
export { Bt as followJobProgress, Qt as islandNames, en as mountIsland, qt as refreshStore, Jt as sidebarHasCatalogContent, Xt as sidebarTagCounts, Kt as storeNames, Yt as syncSidebarSurface, tn as unmountIsland, zt as watchJob };
