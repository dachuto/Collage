#pragma once

#include <array>
#include <cstdio>
#include <regex>
#include <string_view>

namespace mtg_api {

template <typename InputIterator, typename OutputIterator>
std::pair<InputIterator, OutputIterator> percent_decode(InputIterator first, InputIterator last, OutputIterator out) {
	auto in = first;
	while (in != last) {
		if (*in == '%') {
			if (std::distance(in, last) > 2) {
				unsigned parsed = 0;
				if (std::sscanf(std::next(in), "%2x", &parsed) != 1) {
					break;
				}
				*out = parsed;
				++in;
				++in;
			} else {
				break;
			}
		} else if (*in == '+') {
			*out = ' ';
		} else {
			*out = *in;
		}
		++out;
		++in;
	}
	return {in, out};
}

template <typename CharT>
std::basic_string_view<CharT> string_view_from_range(CharT const *first, CharT const *last) {
	return {first, static_cast<std::size_t>(std::distance(first, last))};
}

template <typename Functor>
void split_into_key_value(std::string_view const &args, Functor f) {
	static std::regex const kv_regex("([^=]*)=([^&]*)&?", std::regex::optimize);

	auto first = std::cregex_iterator(args.begin(), args.end(), kv_regex);
	auto last = std::cregex_iterator();

	auto const view_from_submatch = [](std::csub_match const &m) -> std::string_view {
		return string_view_from_range(m.first, m.second);//{m.first, static_cast<std::size_t>(m.length())};
	};

	for (auto it = first; it != last; ++it) {
		f(view_from_submatch((*it)[1]), view_from_submatch((*it)[2]));
	}
}

template <typename Functor>
void args_into_decoded_pairs(std::string_view const &args, Functor f) {
	constexpr std::size_t buffer_size = 2048;
	using buffer_type = std::array<char, buffer_size>;
	buffer_type key_buffer;
	buffer_type value_buffer;
	auto const decode_and_pass = [&f, &key_buffer, &value_buffer](std::string_view const &key, std::string_view const &value) {
		auto const key_its = percent_decode(std::cbegin(key), std::cend(key), std::begin(key_buffer));
		auto const value_its = percent_decode(std::cbegin(value), std::cend(value), std::begin(value_buffer));
		f(string_view_from_range(std::cbegin(key_buffer), key_its.second), string_view_from_range(std::cbegin(value_buffer), value_its.second));
	};
	split_into_key_value(args, decode_and_pass);
}

}
